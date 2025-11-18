from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")

client = OpenAI(api_key=API_KEY, base_url="https://ai.hackclub.com/proxy/v1")


def review_pr(review_prompt, pr_body, pr_title, preferences=""):
    try:
        with open("System_Prompt.md", "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()
    except FileNotFoundError:
        print("Error: The file 'System_Prompt.md' was not found.")
        system_prompt = "You are an expert code reviewer AI."
    except Exception as e:
        print(f"An error occurred: {e}")
        system_prompt = "You are an expert code reviewer AI."

    if preferences:
        system_prompt = f"Please follow these project preferences:\n{preferences}\n\n---\n\n{system_prompt}"

    user_prompt = f"PR Title: {pr_title}\n\nPR Body: {pr_body}\n\n{review_prompt}"
    return generate_review(user_prompt, system_prompt)


def review_comment(comment_body, diff_hunk=None):
    system_prompt = "You are a helpful AI assistant. A user has mentioned you in a code review comment, please respond to them."
    if diff_hunk:
        user_prompt = f"The user commented:\n{comment_body}\n\nThe code they are commenting on is:\n{diff_hunk}"
    else:
        user_prompt = comment_body
    return generate_review(user_prompt, system_prompt)


def generate_review(user_prompt, system_prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": f"{system_prompt}"},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating review: {e}")
        return "Sorry, I encountered an error while generating a response."