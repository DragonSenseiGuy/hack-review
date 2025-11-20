import logging
import os
import re
from dotenv import load_dotenv
from flask import Flask, request
import requests

from github_app import get_installation_token
from preferences import extract_and_save_preference
from review import review_pr, review_comment

load_dotenv()
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BOT_NAME = os.getenv("BOT_NAME")


@app.post("/webhook")
def webhook():
    event = request.headers.get("X-GitHub-Event")
    body = request.json

    # Ignore comments made by the bot itself to prevent loops
    sender = body.get("sender", {}).get("login")
    if sender and sender.lower() == BOT_NAME.lower():
        logging.info(f"Ignoring event triggered by the bot itself ({sender}).")
        return "Ignoring own event"

    if event == "issue_comment" and body["action"] == "created":
        comment_body = body["comment"]["body"].strip()
        pr_number = body["issue"]["number"]
        owner = body["repository"]["owner"]["login"]
        repo = body["repository"]["name"]
        installation_id = body["installation"]["id"]
        token = get_installation_token(installation_id)

        if comment_body == "/review":
            handle_review_command(owner, repo, pr_number, token)
        elif f"@{BOT_NAME.lower()}" in comment_body.lower():
            handle_issue_comment(owner, repo, pr_number, comment_body, token)

    elif event == "pull_request_review_comment" and body["action"] == "created":
        if f"@{BOT_NAME.lower()}" in body["comment"]["body"].lower():
            installation_id = body["installation"]["id"]
            token = get_installation_token(installation_id)
            owner = body["repository"]["owner"]["login"]
            repo = body["repository"]["name"]
            pr_number = body["pull_request"]["number"]
            comment_body = body["comment"]["body"]
            comment_id = body["comment"]["id"]
            diff_hunk = body["comment"]["diff_hunk"]
            handle_review_comment(
                owner, repo, pr_number, comment_body, comment_id, token, diff_hunk
            )

    return "Request received"


def handle_review_command(owner, repo, pr_number, token):
    """
    Handles a command to trigger a full PR review.
    """
    headers = {"Authorization": f"token {token}"}
    
    logging.info(f"Handling /review command for {owner}/{repo} PR #{pr_number}")

    try:
        # Get PR data to find the head SHA, title, and body
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=headers)
        pr_response.raise_for_status()  # Check for errors
        pr_data = pr_response.json()

        pr_body = pr_data.get("body", "")
        pr_title = pr_data.get("title", "")
        commit_id = pr_data.get("head", {}).get("sha")

        if not commit_id:
            logging.error(f"Could not find head SHA for PR #{pr_number}")
            return

        # This is the existing function that does the review
        send_review(owner, repo, pr_number, pr_body, pr_title, token, commit_id)
        logging.info(f"Successfully triggered review for PR #{pr_number}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch PR data for review. Error: {e}")
        logging.error(f"Response body: {e.response.text if e.response else 'No response'}")


def handle_issue_comment(owner, repo, pr_number, comment_body, token):
    if f"@{BOT_NAME.lower()}" not in comment_body.lower():
        logging.warning("handle_issue_comment called without a bot mention. Skipping.")
        return

    headers = {"Authorization": f"token {token}"}
    
    logging.info(f"Handling issue comment for {owner}/{repo} PR #{pr_number}")
    
    preference_response = extract_and_save_preference(comment_body)
    review_response = review_comment(comment_body)
    
    if preference_response:
        response_body = f"{preference_response}\n\n---\n\n{review_response}"
    else:
        response_body = review_response
    
    comment_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    )
    
    try:
        api_response = requests.post(comment_url, headers=headers, json={"body": response_body})
        api_response.raise_for_status()  # Raise an exception for bad status codes
        logging.info(f"Successfully posted comment to PR #{pr_number}. Status: {api_response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post comment to PR #{pr_number}. Error: {e}")
        logging.error(f"Response body: {e.response.text if e.response else 'No response'}")


def handle_review_comment(
    owner, repo, pr_number, comment_body, comment_id, token, diff_hunk
):
    if f"@{BOT_NAME.lower()}" not in comment_body.lower():
        logging.warning("handle_review_comment called without a bot mention. Skipping.")
        return

    headers = {"Authorization": f"token {token}"}
    
    logging.info(f"Handling review comment for {owner}/{repo} PR #{pr_number}")
    
    preference_response = extract_and_save_preference(comment_body)
    review_response = review_comment(comment_body, diff_hunk)
    
    if preference_response:
        response_body = f"{preference_response}\n\n---\n\n{review_response}"
    else:
        response_body = review_response
    
    comment_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies"
    
    try:
        api_response = requests.post(comment_url, headers=headers, json={"body": response_body})
        api_response.raise_for_status()
        logging.info(f"Successfully posted reply to comment {comment_id} in PR #{pr_number}. Status: {api_response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to post reply to comment {comment_id} in PR #{pr_number}. Error: {e}")
        logging.error(f"Response body: {e.response.text if e.response else 'No response'}")


def send_review(owner, repo, pr_number, pr_body, pr_title, token, commit_id):
    headers = {"Authorization": f"token {token}"}

    # Fetch files from the pull request
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files = requests.get(files_url, headers=headers).json()

    try:
        with open("../../data/preferences.md", "r") as f:
            preferences = f.read()
    except FileNotFoundError:
        preferences = ""

    # Generate summary of changes
    summary = summarize_changes(files, pr_body, pr_title, preferences)

    # Post review comments
    post_review_comments(owner, repo, pr_number, commit_id, summary, headers)


def post_review_comments(owner, repo, pr_number, commit_id, summary, headers):
    comments = parse_review_comments(summary)
    for comment in comments:
        comment_url = (
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        )
        payload = {
            "body": comment["comment"],
            "commit_id": commit_id,
            "path": comment["file"],
            "line": comment["line"],
        }
        requests.post(comment_url, headers=headers, json=payload)


def parse_review_comments(summary):
    """
    Parses the review summary to extract individual comments.
    """
    # The regex looks for a pattern like: `* **app.py:42** - The comment text.`
    comment_pattern = re.compile(r"\*\s*\*\*(.+?):(\d+)\*\* - (.+)")
    comments = []
    for line in summary.splitlines():
        match = comment_pattern.match(line)
        if match:
            comments.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "comment": match.group(3),
                }
            )
    return comments


def summarize_changes(files, pr_body, pr_title, preferences):
    """
    Generates a summary of the changes in a pull request.
    """
    keys_to_remove = ["sha", "blob_url", "raw_url", "contents_url"]
    for file in files:
        for key in keys_to_remove:
            file.pop(key, None)

    review_prompt = ""
    for file in files:
        review_prompt += f"\nFile Name: \n{file['filename']} \nStatus: {file['status']}\nAdditions: {file['additions']}\nDeletions: {file['deletions']}\nChanges: {file['changes']}\nDiff: {file['patch']}"
    summary = review_pr(review_prompt, pr_body, pr_title, preferences)
    return summary


if __name__ == "__main__":
    app.run(port=3000, debug=True)
