from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")

if API_KEY:
    client = OpenAI(api_key=API_KEY, base_url="https://ai.hackclub.com/proxy/v1")
else:
    client = None


def review_pr(review_prompt, pr_body, pr_title, preferences=""):
    if not client:
        return "The API_KEY is not configured."
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        system_prompt_path = os.path.join(dir_path, "..", "..", "data", "System_Prompt.md")
        with open(system_prompt_path, "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()
    except FileNotFoundError:
        print("Error: The file 'data/System_Prompt.md' was not found.")
        system_prompt = "You are an expert code reviewer AI."
    except Exception as e:
        print(f"An error occurred: {e}")
        system_prompt = "You are an expert code reviewer AI."

    if preferences:
        system_prompt = f"Please follow these project preferences:\n{preferences}\n\n---\n\n{system_prompt}"

    user_prompt = f"PR Title: {pr_title}\n\nPR Body: {pr_body}\n\n{review_prompt}"
    return generate_review(user_prompt, system_prompt)


def review_comment(comment_body, diff_hunk=None):
    if not client:
        return "The API_KEY is not configured."
    system_prompt = "You are a helpful AI assistant. A user has mentioned you in a code review comment, please respond to them."
    if diff_hunk:
        user_prompt = f"The user commented:\n{comment_body}\n\nThe code they are commenting on is:\n{diff_hunk}"
    else:
        user_prompt = comment_body
    return generate_review(user_prompt, system_prompt)


def generate_review(user_prompt, system_prompt):
    if not client:
        return "The API_KEY is not configured."
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