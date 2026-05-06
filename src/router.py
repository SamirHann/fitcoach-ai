#!/usr/bin/env python3
"""Orchestrateur LangGraph : route les questions vers RAG, Tools ou Chat via LLM."""

import os
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

from memory import ConversationMemory
from agent_rag import RAGAgent
from agent_tools import ToolsAgent
from agent_chat import ChatAgent

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

ROUTING_PROMPT = """Tu es un routeur pour FitCoach AI, assistant musculation.
Classe le message dans une des 3 catégories :

- chat  : salutation, remerciement, question sur l'assistant, conversation générale
- tools : calcul fitness (1RM, TDEE, calories, macros) ou recherche web / études récentes
          → INCLUT les corrections ou précisions sur un calcul précédent (activité, objectif, etc.)
- rag   : question sur l'entraînement, exercices, programmes, nutrition sportive

{history}

Nouveau message : {question}

Réponds UNIQUEMENT par "ROUTE: chat", "ROUTE: tools" ou "ROUTE: rag". Rien d'autre."""

# Fallback mots-clés si le LLM de routage échoue
_TOOLS_KW = (
    "calcul", "calculer", "calcule", "tdee", "1rm", "one rep max",
    "calories", "macros", "macro", "protéines", "glucides", "lipides",
    "kg ×", "kg x", "reps", "répétitions",
    "cherche", "recherche", "étude", "récent", "dernières nouvelles",
    "actualité", "news", "2024", "2025",
)
_CHAT_KW = (
    "bonjour", "salut", "bonsoir", "hello", "coucou", "hey",
    "merci", "super", "parfait", "ok", "okay", "d'accord",
    "au revoir", "bye", "à bientôt", "bonne journée",
    "comment tu", "comment vas", "ça va", "comment t'appelles",
    "qui es-tu", "qu'est-ce que tu es", "présente-toi",
)


class RouterState(TypedDict):
    question: str
    agent: str
    answer: str


def _fallback_route(question: str) -> Literal["rag", "tools", "chat"]:
    q = question.lower()
    if any(kw in q for kw in _CHAT_KW):
        return "chat"
    if any(kw in q for kw in _TOOLS_KW):
        return "tools"
    return "rag"


def _llm_route(question: str, llm: OllamaLLM, history: str = "") -> Literal["rag", "tools", "chat"] | None:
    """Retourne la décision LLM ou None si ambiguë/erreur."""
    try:
        prompt = ROUTING_PROMPT.format(question=question, history=history)
        decision = llm.invoke(prompt).strip().lower()
        if "chat" in decision:
            return "chat"
        if "tools" in decision:
            return "tools"
        if "rag" in decision:
            return "rag"
    except Exception as e:
        print(f"[Routeur] ⚠ Erreur LLM ({e}), fallback mots-clés")
    return None


def build_graph(memory: ConversationMemory) -> StateGraph:
    rag_agent = RAGAgent(memory=memory)
    tools_agent = ToolsAgent(memory=memory)
    chat_agent = ChatAgent(memory=memory)
    llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

    def router_node(state: RouterState) -> RouterState:
        question = state["question"]
        history = memory.get_context_string()
        agent = _llm_route(question, llm, history)
        if agent is None:
            print("[Routeur] ⚠ Décision LLM ambiguë, fallback mots-clés")
            agent = _fallback_route(question)
        labels = {"rag": "RAG", "tools": "Tools", "chat": "Chat"}
        print(f"\n[Routeur] → Agent choisi : {labels[agent]}")
        return {**state, "agent": agent}

    def rag_node(state: RouterState) -> RouterState:
        return {**state, "answer": rag_agent.run(state["question"])}

    def tools_node(state: RouterState) -> RouterState:
        return {**state, "answer": tools_agent.run(state["question"])}

    def chat_node(state: RouterState) -> RouterState:
        return {**state, "answer": chat_agent.run(state["question"])}

    graph = StateGraph(RouterState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("tools", tools_node)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda state: state["agent"],
        {"rag": "rag", "tools": "tools", "chat": "chat"},
    )
    graph.add_edge("rag", END)
    graph.add_edge("tools", END)
    graph.add_edge("chat", END)

    return graph.compile()
