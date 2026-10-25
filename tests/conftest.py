import os

# Tests kabhi real OpenAI call nahi karte — CI me asli key ki zarurat nahi
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
