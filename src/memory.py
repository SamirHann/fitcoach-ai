#!/usr/bin/env python3
"""Mémoire conversationnelle : fenêtre glissante des 3 derniers échanges."""

from collections import deque


class ConversationMemory:
    def __init__(self, max_turns: int = 3):
        self._turns = deque(maxlen=max_turns)

    def add(self, question: str, answer: str) -> None:
        self._turns.append({"question": question, "answer": answer})

    def get_context_string(self) -> str:
        if not self._turns:
            return ""
        lines = ["--- Historique de la conversation ---"]
        for i, turn in enumerate(self._turns, 1):
            lines.append(f"[Tour {i}] Utilisateur : {turn['question']}")
            lines.append(f"[Tour {i}] Assistant   : {turn['answer']}")
        lines.append("--- Fin de l'historique ---")
        return "\n".join(lines)

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
