#!/usr/bin/env python3
"""Orchestrateur LangGraph : route les questions vers RAG ou Tools."""

import os
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from memory import ConversationMemory
from agent_rag import RAGAgent
from agent_tools import ToolsAgent

load_dotenv()

TOOLS_KEYWORDS = (
    "calcul", "calculer", "calcule", "tdee", "1rm", "one rep max",
    "calories", "macros", "macro", "protéines", "glucides", "lipides",
    "kg ×", "kg x", "reps", "répétitions",
    "cherche", "recherche", "étude", "récent", "dernières nouvelles",
    "actualité", "news", "2024", "2025",
)


class RouterState(TypedDict):
    question: str
    agent: str
    answer: str


def _choose_agent(question: str) -> Literal["rag", "tools"]:
    q = question.lower()
    if any(kw in q for kw in TOOLS_KEYWORDS):
        return "tools"
    return "rag"


def build_graph(memory: ConversationMemory) -> StateGraph:
    rag_agent = RAGAgent(memory=memory)
    tools_agent = ToolsAgent(memory=memory)

    def router_node(state: RouterState) -> RouterState:
        agent = _choose_agent(state["question"])
        print(f"\n[Routeur] → Agent choisi : {'RAG' if agent == 'rag' else 'Tools'}")
        return {**state, "agent": agent}

    def rag_node(state: RouterState) -> RouterState:
        answer = rag_agent.run(state["question"])
        return {**state, "answer": answer}

    def tools_node(state: RouterState) -> RouterState:
        answer = tools_agent.run(state["question"])
        return {**state, "answer": answer}

    def route_decision(state: RouterState) -> str:
        return state["agent"]

    graph = StateGraph(RouterState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("tools", tools_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_decision, {"rag": "rag", "tools": "tools"})
    graph.add_edge("rag", END)
    graph.add_edge("tools", END)

    return graph.compile()
