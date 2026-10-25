"""Saari settings environment variables se — code me koi secret nahi."""
import os

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
APP_VERSION = os.getenv("APP_VERSION", "local")   # CI/CD pipeline git commit SHA set karegi
