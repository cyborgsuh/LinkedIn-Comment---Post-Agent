import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("UNIPILE_DSN")
API_KEY = os.getenv("X-API-KEY")

HEADERS = {
    "X-API-KEY": API_KEY,
    "accept": "application/json",
    "content-type": "application/json"
}

def _url(path: str):
    return f"{BASE_URL}{path}"

# ---------------- LINKEDIN SEARCH ----------------
def linkedin_search(account_id: str, keywords: str, limit: int = 5):
    """Search LinkedIn posts using keywords via Unipile."""
    url = _url(f"/api/v1/linkedin/search?account_id={account_id}")
    payload = {"api": "classic", "category": "posts", "keywords": keywords, "limit": limit}
    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json().get("items", [])

# ---------------- COMMENT ----------------
def comment_on_post(post_social_id: str, text: str, account_id: str):
    """Comment on a LinkedIn post using social_id."""
    # strip URN prefix
    if not post_social_id:
        raise ValueError("Missing social_id")
    if not text or len(text) > 1250:
        raise ValueError("Comment text invalid length")

    url = _url(f"/api/v1/posts/{post_social_id}/comments")
    data = {"account_id": account_id, "text": text}

    r = requests.post(url, headers=HEADERS, json=data)
    r.raise_for_status()
    return r.json()


def create_post(account_id: str, text: str):
    url = _url("/api/v1/posts")
    # multipart/form-data
    files = {
        "account_id": (None, account_id),
        "text": (None, text)
    }
    r = requests.post(url, headers={"X-API-KEY": API_KEY, "accept": "application/json"}, files=files)
    r.raise_for_status()
    return r.json()
    