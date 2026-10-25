"""FastAPI backend + Gradio UI.
  GET  /health  → load balancer / CI smoke test
  POST /chat    → REST API (Postman / frontend)
  GET  /        → Gradio chat UI
"""
import uuid

import gradio as gr
from fastapi import FastAPI
from pydantic import BaseModel

from app import agent
from app.config import APP_VERSION
from app.tools import TICKETS

api = FastAPI(title="ShopEase Support Agent", version=APP_VERSION)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


@api.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}


@api.post("/chat")
def chat_endpoint(req: ChatRequest):
    return agent.chat(req.message, req.thread_id)


@api.get("/tickets")
def list_tickets():
    return TICKETS


def respond(message, history, request: gr.Request):
    thread = getattr(request, "session_hash", None) or str(uuid.uuid4())
    return agent.chat(message, thread_id=f"ui-{thread}")["answer"]


demo = gr.ChatInterface(
    respond,
    title=f"🎫 ShopEase Support Agent ({APP_VERSION})",
    examples=["What is the refund policy?", "Mujhe damaged product mila hai",
              "Status of TKT-1002?", "How long does express delivery take?"],
)

app = gr.mount_gradio_app(api, demo, path="/")
