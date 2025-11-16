from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://ai.hackclub.com/proxy/v1"
)

def review_pr(review_prompt, pr_body, pr_title):
    try:
        with open("System_Prompt.md", "r") as system_prompt_file:
            system_prompt = system_prompt_file.read()
    except FileNotFoundError:
        print("Error: The file 'System_Prompt.md' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    user_prompt = f"PR Title: {pr_title}\n\nPR Body: {pr_body}\n\n{review_prompt}"
    print(user_prompt)

    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-0905",
        messages=[
            {"role": "developer", "content": f"{system_prompt}"},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content