import os
import webbrowser
from praw import Reddit

# ───────────────────────────────────────────────────────────────────────────────
# 1️⃣ Load your credentials from environment
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")
REDIRECT_URI = "http://localhost:65010/authorize_callback"
# ───────────────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────────
# 2️⃣ Initialize PRAW without user/pass
reddit = Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    user_agent=USER_AGENT,
)
# ───────────────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────────
# 3️⃣ Build the OAuth URL (permanent = gives you a refresh token)
scopes = ["read", "submit"]
state = "random_state_string"
auth_url = reddit.auth.url(scopes, state, "permanent")
# ───────────────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────────
#  Ensure Chrome is used to open the URL:
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(chrome_path):
    webbrowser.register(
        "chrome", None, webbrowser.BackgroundBrowser(f'"{chrome_path}"')
    )
    webbrowser.get("chrome").open(auth_url)
else:
    # fallback
    webbrowser.open(auth_url)
# ───────────────────────────────────────────────────────────────────────────────

print(">>> 1. If the browser didn’t open automatically, visit:\n", auth_url, "\n")

# ───────────────────────────────────────────────────────────────────────────────
# 4️⃣ After you approve, Reddit redirects here with ?code=…  Copy that code:
code = input(">>> 2. Paste the `code` parameter from the redirected URL here: ").strip()
# ───────────────────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────────
# 5️⃣ Exchange code for a refresh token
refresh_token = reddit.auth.authorize(code)
print("\n✅ Your refresh token is:\n", refresh_token)
# ───────────────────────────────────────────────────────────────────────────────
