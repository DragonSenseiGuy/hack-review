from flask import Flask, request
from github_app import get_installation_token
from review import review_pr
import requests
import os
from dotenv import load_dotenv

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

        send_review(owner, repo, pr_number, pr_body, pr_title, token)

    return "Request received, sending review"


def send_review(owner, repo, pr_number, pr_body, pr_title, token):
    headers = {"Authorization": f"token {token}"}

    # Fetch files from the pull request
    files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files = requests.get(files_url, headers=headers).json()

    # Generate summary of changes
    summary = summarize_changes(files, pr_body, pr_title)

    # Post comment
    comment_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    )
    requests.post(comment_url, headers=headers, json={"body": summary})


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

