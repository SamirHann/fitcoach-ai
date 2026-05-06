#!/usr/bin/env python3
"""FitCoach AI — CLI principale."""

import sys
from dotenv import load_dotenv

load_dotenv()

from memory import ConversationMemory
from router import build_graph

BANNER = """
╔══════════════════════════════════════════╗
║           FitCoach AI  🏋️               ║
║  Assistant musculation multi-agents      ║
╚══════════════════════════════════════════╝
Commandes : 'exit' pour quitter | 'clear' pour vider la mémoire
"""


def main():
    print(BANNER)

    memory = ConversationMemory(max_turns=3)
    graph = build_graph(memory)

    while True:
        try:
            question = input("Vous: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir !")
            break

        if not question:
            continue

        if question.lower() == "exit":
            print("Au revoir !")
            break

        if question.lower() == "clear":
            memory.clear()
            print("→ Mémoire conversationnelle effacée.\n")
            continue

        try:
            result = graph.invoke({
                "question": question,
                "agent": "",
                "answer": "",
            })
            answer = result.get("answer", "Erreur : aucune réponse générée.")
        except Exception as e:
            print(f"✗ Erreur : {e}", file=sys.stderr)
            continue

        print(f"\n[Final] → {answer}\n")
        memory.add(question, answer)


if __name__ == "__main__":
    main()
