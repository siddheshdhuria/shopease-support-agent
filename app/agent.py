"""LangGraph agent: START → agent ⇄ tools → END"""
from functools import lru_cache

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import CHAT_MODEL
from app.tools import TOOLS

SYSTEM_PROMPT = """You are ShopEase's customer support agent.

Rules:
1. For any policy/process question, ALWAYS call search_knowledge_base first. Answer only from retrieved documents; cite the KB id like [KB001].
2. If the customer reports a problem needing action (damaged item, missing refund, money deducted, etc.), create a ticket.
   Ask for the customer's name first if you don't know it.
3. Priority: damaged/wrong product or money deducted = high; fraud/legal threat = urgent (then escalate); general = medium/low.
4. Use get_ticket_status when a ticket ID is mentioned.
5. Escalate to a human for fraud, legal threats, or very angry customers with repeated problems.
6. If the knowledge base has no answer, say so honestly and offer to create a ticket. Never make up policies.
7. Reply in the same language the customer uses (English, Hindi or Hinglish). Be short, polite and clear.
"""


@lru_cache(maxsize=1)
def get_graph():
    from langchain_openai import ChatOpenAI

    llm_with_tools = ChatOpenAI(model=CHAT_MODEL, temperature=0).bind_tools(TOOLS)

    def agent_node(state: MessagesState):
        response = llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=MemorySaver())


def chat(message: str, thread_id: str = "default") -> dict:
    """Ek user message → agent ka final answer + is turn me kaunse tools call hue."""
    graph = get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    before = len(graph.get_state(config).values.get("messages", []))
    result = graph.invoke({"messages": [("user", message)]}, config)
    new_messages = result["messages"][before:]

    tool_calls = [{"name": tc["name"], "args": tc["args"]}
                  for m in new_messages if isinstance(m, AIMessage) for tc in m.tool_calls]
    tool_results = [m.name for m in new_messages if isinstance(m, ToolMessage)]
    return {"answer": result["messages"][-1].content, "tool_calls": tool_calls,
            "tools_executed": tool_results, "thread_id": thread_id}
