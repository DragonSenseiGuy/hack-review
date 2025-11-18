from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")

client = OpenAI(api_key=API_KEY, base_url="https://ai.hackclub.com/proxy/v1")

def extract_and_save_preference(comment_body):
    """
    Analyzes a comment to see if it contains a project preference, and if so,
    saves it to the preferences.md file.
    """
    system_prompt = """You are an AI assistant tasked with identifying project-specific preferences from user comments.
Analyze the following comment. If it contains a clear preference, convention, or rule for the project's codebase, please summarize it in a single, concise sentence.
For example, if the user says 'we should always use tabs instead of spaces', you should output 'Use tabs instead of spaces for indentation.'
If the comment does not contain a clear preference, respond with 'NO_PREFERENCE'.
Do not add any other text to your response."""

    user_prompt = f"Here is the comment: '{comment_body}'"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    
    preference = response.choices[0].message.content.strip()

    if "NO_PREFERENCE" not in preference:
        with open("preferences.md", "a") as f:
            f.write(f"- {preference}\n")
        return f"Preference noted: {preference}"
    else:
        return "Thanks for your feedback!"
