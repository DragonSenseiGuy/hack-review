from flask import Flask, request
from github_app import get_installation_token
from review import review_pr
import requests
import os
from dotenv import load_dotenv
import re

load_dotenv()
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.post("/webhook")
def webhook():
    event = request.headers.get("X-GitHub-Event")
    body = request.json

    if event == "pull_request" and body["action"] == "opened":
        installation_id = body["installation"]["id"]
        token = get_installation_token(installation_id)

        owner = body["repository"]["owner"]["login"]
        repo = body["repository"]["name"]
        pr_number = body["number"]
        pr_body = body["pull_request"]["body"]
        pr_title = body["pull_request"]["title"]
        commit_id = body["pull_request"]["head"]["sha"]

        send_review(owner, repo, pr_number, pr_body, pr_title, token, commit_id)

    return "Request received, sending review"


def send_review(owner, repo, pr_number, pr_body, pr_title, token, commit_id):
    headers = {"Authorization": f"token {token}"}

    # Fetch files from the pull request
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files = requests.get(files_url, headers=headers).json()

    # Generate summary of changes
    summary = summarize_changes(files, pr_body, pr_title)

    # Post review comments
    post_review_comments(owner, repo, pr_number, commit_id, summary, headers)


def post_review_comments(owner, repo, pr_number, commit_id, summary, headers):
    comments = parse_review_comments(summary)
    for comment in comments:
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
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
                {"file": match.group(1), "line": int(match.group(2)), "comment": match.group(3)}
            )
    return comments


def summarize_changes(files, pr_body, pr_title):
    """
    Generates a summary of the changes in a pull request.
    """
    keys_to_remove = ["sha", "blob_url", "raw_url", "contents_url"]
    for file in files:
        for key in keys_to_remove:
            file.pop(key, None)
    print(files)

    review_prompt = ""
    for file in files:
        review_prompt += f"\nFile Name: \n{file['filename']} \nStatus: {file['status']}\nAdditions: {file['additions']}\nDeletions: {file['deletions']}\nChanges: {file['changes']}\nDiff: {file['patch']}"
    summary = review_pr(review_prompt, pr_body, pr_title)
    return summary


if __name__ == "__main__":
    app.run(port=3000, debug=True)
