from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Literal
from tools_unipile import fetch_search_posts, filter_relevant, safe_comment, safe_post_motivational
from langgraph.store.memory import InMemoryStore
from langchain_groq import ChatGroq
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("LINKEDIN_UNIPILE_ACCOUNT_ID")

# ---------------- STATE ----------------
class State(TypedDict):
    posts: List[dict]
    relevant_posts: List[dict]
    command: str
    action: Literal["comment_latest", "preview_latest", "motivational_post", "unknown"]

MEMORY_FILE = "agent_memory.json"

# ---------------- PERSISTENT MEMORY ----------------
class FileMemory:
    def __init__(self, path=MEMORY_FILE):
        self.path = path
        self.state = {}
        self.load_state()

    def load_state(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self.state = json.load(f)
        else:
            self.state = {"seen_posts": {}}
        return self.state

    def save_state(self, state=None):
        if state is not None:
            self.state = state
        with open(self.path, "w") as f:
            json.dump(self.state, f, indent=2)

memory = FileMemory()

# ---------------- NODES ----------------
def node_fetch(state: State):
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.4)
    prompt = "Suggest 3 short LinkedIn search keywords relevant to AI, startups, and building."
    keywords = llm.invoke(prompt).content.strip().replace("\n", ", ")
    print(f"AI Keywords: {keywords}")
    posts = fetch_search_posts(keywords, limit=10)
    return {"posts": posts}

def node_filter(state: State):
    relevant = filter_relevant(state["posts"])
    return {"relevant_posts": relevant}

def node_comment(state: State):
    seen_posts = memory.state.get("seen_posts", {})
    for post in state["relevant_posts"]:
        post_id = str(post.get("social_id") or post.get("id"))
        if seen_posts.get(post_id):
            print(f"Skipping already-seen post {post_id}")
            continue
        safe_comment(post)
        seen_posts[post_id] = True
    memory.state["seen_posts"] = seen_posts
    memory.save_state()
    return {}

def node_weekly_post(state: State):
    topic = "building in tech and AI"
    safe_post_motivational(ACCOUNT_ID, topic)
    return {}

def node_preview(state: State):
    print("\n=== RELEVANT POSTS ===")
    for i, post in enumerate(state["relevant_posts"]):
        print(f"{i}. ID: {post['id']}, Social ID: {post['social_id']}, Reactions: {post.get('reaction_counter',0)}, Comments: {post.get('comment_counter',0)}")
        print(post["text"][:100])
        print("-----")
    return {}

def node_router(state: State):
    cmd = state["command"].lower()
    if "comment" in cmd:
        return {"action": "comment_latest"}
    elif "preview" in cmd:
        return {"action": "preview_latest"}
    elif "weekly" in cmd or "motivation" in cmd:
        return {"action": "motivational_post"}
    else:
        return {"action": "unknown"}

# ---------------- GRAPH ----------------
graph = StateGraph(State)
graph.add_node("router", node_router)
graph.add_node("fetch", node_fetch)
graph.add_node("filter", node_filter)
graph.add_node("comment", node_comment)
graph.add_node("preview", node_preview)
graph.add_node("weekly_post", node_weekly_post)

# Route first to decide what to do
graph.set_entry_point("router")

def route_initial(state: State):
    """Route from start to either fetch (comment/preview) or direct to post (weekly)"""
    action = state["action"]
    if action == "comment_latest" or action == "preview_latest":
        return "fetch"
    elif action == "motivational_post":
        return "weekly_post"
    else:
        return END

# From router, decide if we need to fetch posts or go straight to post
graph.add_conditional_edges("router", route_initial)

# Fetch -> Filter -> Route to comment/preview
graph.add_edge("fetch", "filter")

def route_after_filter(state: State):
    action = state["action"]
    if action == "comment_latest":
        return "comment"
    elif action == "preview_latest":
        return "preview"
    else:
        return END

graph.add_conditional_edges("filter", route_after_filter)
graph.add_edge("comment", END)
graph.add_edge("preview", END)
graph.add_edge("weekly_post", END)

store = InMemoryStore()
app = graph.compile(store=store)

# ---------------- CLI ----------------
def cli():
    print("LangGraph LinkedIn Agent (Search + Groq LLM)")
    print("Commands: comment latest | preview latest | motivational post | exit")
    while True:
        cmd = input("Agent> ")
        if cmd.lower() == "exit":
            break
        state = memory.load_state()
        state.setdefault("posts", [])
        state.setdefault("relevant_posts", [])
        state["command"] = cmd
        state.setdefault("action", "unknown")
        app.invoke(state)
        memory.save_state(state)

if __name__ == "__main__":
    cli()