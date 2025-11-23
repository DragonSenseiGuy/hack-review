import jwt
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
# Construct the path to the private key file relative to this script
dir_path = os.path.dirname(os.path.realpath(__file__))
private_key_path = os.path.join(dir_path, "..", "..", "hack-review.pem")

with open(private_key_path, "r") as f:
    PRIVATE_KEY = f.read()

def generate_jwt():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def get_installation_token(installation_id):
    """
    Generates a token for an installation
    :param installation_id:
    :return token:
    """
    jwt_token = generate_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
    r = requests.post(url, headers=headers)
    return r.json()["token"]
