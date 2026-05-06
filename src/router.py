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

CHAT_KEYWORDS = (
    "bonjour", "salut", "bonsoir", "hello", "coucou", "hey",
    "merci", "super", "parfait", "ok", "okay", "d'accord",
    "au revoir", "bye", "à bientôt", "bonne journée",
    "comment tu vas", "comment vas-tu", "ça va", "comment tu t'appelles",
    "qui es-tu", "qu'est-ce que tu es", "présente-toi",
)


class RouterState(TypedDict):
    question: str
    agent: str
    answer: str


CHAT_RESPONSES = {
    "bonjour": "Bonjour ! Je suis FitCoach AI, ton assistant musculation. Pose-moi une question sur l'entraînement, la nutrition ou demande-moi un calcul (1RM, TDEE, macros) !",
    "salut":   "Salut ! Prêt à t'aider sur tout ce qui touche à la musculation et la nutrition sportive.",
    "merci":   "Avec plaisir ! N'hésite pas si tu as d'autres questions sur l'entraînement ou la nutrition.",
    "au revoir": "À bientôt ! Bon entraînement !",
    "bye":       "À bientôt ! Bon entraînement !",
    "default":   "Je suis FitCoach AI, ton assistant spécialisé en musculation et nutrition sportive. Comment puis-je t'aider ?",
}


def _choose_agent(question: str) -> Literal["rag", "tools", "chat"]:
    q = question.lower()
    if any(kw in q for kw in CHAT_KEYWORDS):
        return "chat"
    if any(kw in q for kw in TOOLS_KEYWORDS):
        return "tools"
    return "rag"


def _chat_response(question: str) -> str:
    q = question.lower()
    for key, response in CHAT_RESPONSES.items():
        if key in q:
            return response
    return CHAT_RESPONSES["default"]


def build_graph(memory: ConversationMemory) -> StateGraph:
    rag_agent = RAGAgent(memory=memory)
    tools_agent = ToolsAgent(memory=memory)

    def router_node(state: RouterState) -> RouterState:
        agent = _choose_agent(state["question"])
        labels = {"rag": "RAG", "tools": "Tools", "chat": "Chat"}
        print(f"\n[Routeur] → Agent choisi : {labels[agent]}")
        return {**state, "agent": agent}

    def rag_node(state: RouterState) -> RouterState:
        answer = rag_agent.run(state["question"])
        return {**state, "answer": answer}

    def tools_node(state: RouterState) -> RouterState:
        answer = tools_agent.run(state["question"])
        return {**state, "answer": answer}

    def chat_node(state: RouterState) -> RouterState:
        answer = _chat_response(state["question"])
        return {**state, "answer": answer}

    def route_decision(state: RouterState) -> str:
        return state["agent"]

    graph = StateGraph(RouterState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("tools", tools_node)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_decision, {"rag": "rag", "tools": "tools", "chat": "chat"})
    graph.add_edge("rag", END)
    graph.add_edge("tools", END)
    graph.add_edge("chat", END)

    return graph.compile()
