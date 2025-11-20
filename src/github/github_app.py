import jwt
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PEM_PATH = os.path.join(ROOT_DIR, 'hack-review.pem')

try:
    with open(PEM_PATH, "r") as pem_file:
        PRIVATE_KEY = pem_file.read()
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {PEM_PATH}. Make sure 'hack-review.pem' is in the project root directory.") from None


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
