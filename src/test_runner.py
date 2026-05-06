#!/usr/bin/env python3
"""Exécute les 6 cas de test (3 RAG + 3 Tools) et capture les sorties.

Génère un fichier test_results.md avec les vraies sorties pour le README.
"""

import io
import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from memory import ConversationMemory
from router import build_graph

TEST_CASES = [
    # === RAG ===
    {
        "agent": "RAG",
        "type": "Nominal",
        "question": "Quelle fréquence pour les pectoraux en programme PPL ?",
        "expected": "Réponse sourcée avec citation [Source: exemple_programme.txt, chunk N]",
    },
    {
        "agent": "RAG",
        "type": "Hors sujet",
        "question": "Quel est le PIB de la France ?",
        "expected": "Refus poli + redirection",
    },
    {
        "agent": "RAG",
        "type": "Hallucination",
        "question": "Quel est le programme d'entraînement personnel de LeBron James ?",
        "expected": "Aveu d'absence de source",
    },
    # === Tools ===
    {
        "agent": "Tools",
        "type": "Nominal",
        "question": "Calcule mon 1RM : 80kg pour 8 reps",
        "expected": "1RM ≈ 106.7 kg (formule Epley)",
    },
    {
        "agent": "Tools",
        "type": "Recherche web",
        "question": "Cherche des études récentes sur la créatine",
        "expected": "3 résultats web pertinents",
    },
    {
        "agent": "Tools",
        "type": "TDEE",
        "question": "Calcule mon TDEE : 75kg, 175cm, 25 ans, homme, modérément actif",
        "expected": "TDEE ≈ 2700-2900 kcal/jour",
    },
]


def run_one(graph, question: str, memory: ConversationMemory) -> dict:
    """Exécute une question, capture stdout (les traces) et la réponse."""
    buf = io.StringIO()
    t0 = time.time()
    try:
        with redirect_stdout(buf):
            result = graph.invoke({
                "question": question,
                "agent": "",
                "answer": "",
            })
        answer = result.get("answer", "")
        error = None
    except Exception as e:
        answer = ""
        error = str(e)

    elapsed = round(time.time() - t0, 1)
    traces = buf.getvalue()
    return {
        "question": question,
        "traces": traces,
        "answer": answer,
        "error": error,
        "elapsed_s": elapsed,
    }


def main():
    print("=" * 70)
    print("FitCoach AI — Test Runner")
    print("=" * 70)

    memory = ConversationMemory()
    graph = build_graph(memory)
    results = []

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {case['agent']} / {case['type']}")
        print(f"Question : {case['question']}")
        print("-" * 70)

        outcome = run_one(graph, case["question"], memory)
        outcome.update({
            "case_id": i,
            "agent": case["agent"],
            "type": case["type"],
            "expected": case["expected"],
        })
        results.append(outcome)

        # Affichage immédiat
        print(outcome["traces"], end="")
        if outcome["error"]:
            print(f"✗ ERREUR : {outcome['error']}")
        else:
            print(f"\n[Final] → {outcome['answer']}")
            print(f"\n⏱ {outcome['elapsed_s']}s")

        # Réinitialiser la mémoire entre les tests pour isoler les cas
        memory.clear()

    # Sauvegarde JSON brute
    out_dir = Path("/app/docs")
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / "test_results.json"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n✓ Résultats JSON : {json_path}")

    # Génère le markdown avec les vrais résultats
    md_lines = ["# Résultats des tests — exécution réelle\n"]
    md_lines.append("## Tests Agent RAG\n")
    md_lines.append("| # | Type | Question | Résultat attendu | Résultat obtenu | Latence | Statut |")
    md_lines.append("|---|------|----------|-----------------|-----------------|---------|--------|")
    for r in results:
        if r["agent"] != "RAG":
            continue
        ans_short = (r["answer"] or r["error"] or "").replace("\n", " ").strip()[:200]
        if len(ans_short) >= 200:
            ans_short += "..."
        status = "✅" if not r["error"] else "❌"
        md_lines.append(
            f"| {r['case_id']} | {r['type']} | {r['question']} | {r['expected']} | {ans_short} | {r['elapsed_s']}s | {status} |"
        )

    md_lines.append("\n## Tests Agent Tools\n")
    md_lines.append("| # | Type | Question | Outil appelé | Résultat attendu | Résultat obtenu | Latence | Statut |")
    md_lines.append("|---|------|----------|-------------|-----------------|-----------------|---------|--------|")
    for r in results:
        if r["agent"] != "Tools":
            continue
        # Détecter l'outil utilisé depuis les traces
        if "calculator appelé" in r["traces"]:
            tool = "calculator"
        elif "web_search appelé" in r["traces"]:
            tool = "web_search"
        else:
            tool = "?"
        ans_short = (r["answer"] or r["error"] or "").replace("\n", " ").strip()[:200]
        if len(ans_short) >= 200:
            ans_short += "..."
        status = "✅" if not r["error"] else "❌"
        md_lines.append(
            f"| {r['case_id']} | {r['type']} | {r['question']} | {tool} | {r['expected']} | {ans_short} | {r['elapsed_s']}s | {status} |"
        )

    md_path = out_dir / "test_results.md"
    md_path.write_text("\n".join(md_lines))
    print(f"✓ Tableau Markdown : {md_path}")
    print("\n" + "=" * 70)
    print(f"Tests terminés : {len(results)} cas exécutés")
    print("=" * 70)


if __name__ == "__main__":
    main()
