#!/usr/bin/env python3
"""Orchestrateur LangGraph : route les questions vers RAG, Tools ou Chat via LLM."""

import os
import re
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
- tools : calcul fitness (1RM, TDEE, calories, macros) OU recherche web/actualités
          → Calculs : contient des chiffres + kg/reps/cm/ans ou mots "1rm","tdee","macros","calories"
          → Web : actualités, études récentes, "2024", "2025", nouvelles, dernières recherches
          → Corrections de calcul : "en fait 5x/semaine", "plutôt actif", "non 3 fois par semaine"
- rag   : question générale sur l'entraînement, exercices, programmes, nutrition sportive
          → inclut : récupération, sommeil sportif, blessures, mobilité, stretching, technique
          → "combien de protéines par jour ?" sans chiffres personnels = rag
          → "quel programme débutant ?" = rag
          → "comment optimiser mon sommeil pour la récupération ?" = rag
          → "je veux grossir", "je veux prendre de la masse", "aide moi à perdre du gras" = rag
          → "le meilleur exercice ?", "quel exercice pour les pecs ?" = rag
          → intentions fitness sans calcul = rag

{history}

Nouveau message : {question}

Réponds UNIQUEMENT par "ROUTE: chat", "ROUTE: tools" ou "ROUTE: rag". Rien d'autre."""

# Regex pour détecter les patterns 1RM naturels : "8 x 80kg", "80kg × 8", "100 kilos 6 fois", etc.
_1RM_RE = re.compile(
    r'\d+\s*(?:x|×|\*)\s*\d+\s*kg'
    r'|\d+\s*kg\s*(?:x|×|\*)\s*\d+'
    r'|\d+[.,]?\d*\s*kilo[s]?\b.{0,15}\d+\s*fois'
    r'|\d+\s*fois\b.{0,15}\d+[.,]?\d*\s*kilo[s]?',
    re.IGNORECASE,
)

# Keywords forts : prennent priorité sur le LLM (sans ambiguïté)
_STRONG_TOOLS_KW = (
    "calcul", "calculer", "calcule", "tdee", "1rm", "one rep max",
    "calories", "macros", "macro",
    "kg ×", "kg x", "reps", "répétitions",
    "x/semaine", "x/sem", "fois par sem", "fois par semaine",
)
# Keywords faibles : utilisés en fallback si LLM échoue
_WEAK_TOOLS_KW = (
    "cherche", "recherche", "étude", "récent", "dernières nouvelles",
    "actualité", "actualités", "actu", "news", "2024", "2025",
)
_CHAT_KW = (
    "bonjour", "salut", "bonsoir", "hello", "coucou", "hey",
    "merci", "super", "parfait", "d'accord",
    "au revoir", "bye", "à bientôt", "bonne journée",
    "comment tu", "comment vas", "ça va", "comment t'appelles",
    "qui es-tu", "qu'est-ce que tu es", "présente-toi",
    "tu peux faire", "tu sais faire", "à quoi tu sers", "tu peux m'aider",
    "tes capacités", "ton rôle", "tu fais quoi", "faire quoi",
)


class RouterState(TypedDict):
    question: str
    agent: str
    answer: str


def _strong_route(question: str) -> Literal["rag", "tools", "chat"] | None:
    """Route déterministe sur keywords forts — bypass le LLM.
    - Tools toujours en premier (regex 1RM + keywords).
    - Chat seulement sur messages courts (≤ 5 mots) : évite que 'parfait,' ou 'super,'
      en début d'une vraie question soient interceptés comme chat."""
    q = question.lower()
    if any(kw in q for kw in _STRONG_TOOLS_KW) or bool(_1RM_RE.search(q)):
        return "tools"
    if any(kw in q for kw in _CHAT_KW) and len(q.split()) <= 5:
        return "chat"
    return None


def _fallback_route(question: str) -> Literal["rag", "tools", "chat"]:
    """Fallback final si LLM échoue ou est ambigu."""
    q = question.lower()
    if any(kw in q for kw in _CHAT_KW):
        return "chat"
    if any(kw in q for kw in _STRONG_TOOLS_KW) or any(kw in q for kw in _WEAK_TOOLS_KW):
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
        labels = {"rag": "RAG", "tools": "Tools", "chat": "Chat"}

        # 1. Keywords forts : déterministes, bypass LLM
        agent = _strong_route(question)
        if agent is not None:
            print(f"\n[Routeur] → Agent choisi : {labels[agent]}")
            return {**state, "agent": agent}

        # 2. LLM pour les cas nuancés
        history = memory.get_context_string()
        agent = _llm_route(question, llm, history)
        if agent is None:
            print("[Routeur] ⚠ Décision LLM ambiguë, fallback mots-clés")
            agent = _fallback_route(question)
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
