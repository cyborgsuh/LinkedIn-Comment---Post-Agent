import random
import time
from unipile_client import linkedin_search, comment_on_post
from langchain_groq import ChatGroq
from unipile_client import create_post
from dotenv import load_dotenv
import os

load_dotenv()

ACCOUNT_ID = os.getenv("LINKEDIN_UNIPILE_ACCOUNT_ID")
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.4)

DRY_RUN = False
MAX_COMMENTS_PER_DAY = 8
RANDOM_SKIP = 0.3
seen_posts = set()

# ---------------- SEARCH POSTS ----------------
def fetch_search_posts(keywords: str, limit=10):
    """
    Search LinkedIn posts using the Unipile API.
    """
    posts = linkedin_search(ACCOUNT_ID, keywords, limit)
    return posts

# ---------------- FILTER RELEVANT ----------------
def filter_relevant(posts):
    """
    Ask AI to decide which posts are worth commenting on.
    """
    relevant = []
    for post in posts:
        text = post.get("text") or ""
        prompt = f"""
You are Suhaib, AI engineer and builder.
Decide if this LinkedIn post is relevant for you to comment on.
Post:
{text}
Answer only "yes" or "no".
"""
        res = llm.invoke(prompt).content.strip().lower()
        if res == "yes":
            relevant.append(post)
    return relevant

# ---------------- GENERATE COMMENT ----------------
def generate_comment(post_text):
    """
    Generates a short LinkedIn comment inspired by the post but not copying it.
    """
    prompt = f"""
You are Suhaib, AI engineer and builder.
Write a short LinkedIn comment:
- human
- reflective
- optimistic
- inspired by the post but do NOT rephrase it
- add your own perspective and insight
- no emojis, no corporate jargon
- keep it under 100 characters

Post:
{post_text}
"""
    comment = llm.invoke(prompt).content.strip()
    # Remove leading/trailing double quotes if present
    if comment.startswith('"') and comment.endswith('"'):
        comment = comment[1:-1]
    return comment

# ---------------- SAFE COMMENT ----------------
def safe_comment(post):
    """
    Post a comment safely:
    - skips already commented posts
    - respects daily limit and human variance
    - tracks seen posts by social_id for uniqueness
    """
    social_id = post.get("social_id") or str(post.get("id"))
    if not social_id:
        print("Skipping post: missing ID")
        return None

    if social_id in seen_posts:
        print(f"Already commented on post {social_id}")
        return None
    if random.random() < RANDOM_SKIP:
        print(f"Skipping post {social_id} for human variance")
        return None
    if len(seen_posts) >= MAX_COMMENTS_PER_DAY:
        print("Reached daily comment limit")
        return None

    comment = generate_comment(post.get("text") or "")
    print("\n=== COMMENT PREVIEW ===")
    print(comment)

    if DRY_RUN:
        print("[DRY_RUN] Not posting")
        seen_posts.add(social_id)
        return comment

    # Random human delay
    time.sleep(random.randint(20, 120))

    # Post comment via Unipile API
    res = comment_on_post(social_id, comment, ACCOUNT_ID)
    seen_posts.add(social_id)
    print(f"Commented on post {social_id}")
    return res

def generate_motivational_post(topic: str = "building in tech and AI"):
    """
    Generate a short, motivational LinkedIn post in Suhaib's tone.
    """
    prompt = f"""
You are Suhaib, an AI engineer and builder.
Write a short LinkedIn post to motivate readers:
- Topic: {topic}
- Tone: human, reflective, motivational, optimistic
- Max 5 sentences
- No corporate buzzwords or emojis
- Include relevant hashtags at the end (max 10)
"""
    res = llm.invoke(prompt).content.strip()
    # Remove leading/trailing double quotes if present
    if res.startswith('"') and res.endswith('"'):
        res = res[1:-1]
    return res

def safe_post_motivational(account_id: str, topic: str = "building in tech and AI"):
    post_text = generate_motivational_post(topic)
    print("\n=== MOTIVATIONAL POST PREVIEW ===")
    print(post_text)

    if DRY_RUN:
        print("[DRY RUN] Not posting")
        return post_text

    # Add a small delay to simulate human posting behavior
    time.sleep(random.randint(20, 60))
    res = create_post(account_id, post_text)
    print("Motivational post published:", res)
    return res