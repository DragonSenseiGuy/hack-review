# Hack Review

Hack Review is a GitHub App that automatically reviews your pull requests. It uses an AI to analyze the changes and provide feedback on potential bugs, style issues, and other problems.

## How it works

1.  When a pull request is opened, the app receives a webhook from GitHub.
2.  The app fetches the files from the pull request.
3.  The app creates a prompt with the PR title, body, and the diffs of the changed files.
4.  The app sends the prompt to [Hack Club's AI API](https://ai.hackclub.com/) to get a review.
5.  The app posts the AI's review as a comment on the pull request.

## Setup

1.  **Create a GitHub App:**
    *   Go to your GitHub settings and create a new GitHub App.
    *   Give it a name, like "Hack Review".
    *   Set the webhook URL to your server's address, e.g., `https://your-domain.com/webhook`.
    *   Create a webhook secret and save it.
    *   Give the app the "Pull requests" read and write permission.
    *   Install the app on the repositories you want it to review.

2.  **Set up the environment:**
    *   Clone this repository.
    *   Create a `.env` file and add the following variables:
        ```
        WEBHOOK_SECRET=<your-webhook-secret>
        APP_ID=<your-app-id>
        API_KEY=<your-api-key>
        ```
    *   Download the private key for your GitHub App and save it as `hack-review.pem` in the root of the project.

3.  **Install the dependencies:**
    ```
    uv sync
    ```

4.  **Run the app:**
    ```
    python app.py
    ```

## System Prompt

The AI's behavior is guided by a system prompt. You can find the system prompt in the `System_Prompt.md` file. You can modify this file to change the AI's behavior.

## How to contribute

1.  Fork the repository.
2.  Create a new branch.
3.  Make your changes.
4.  Open a pull request.
