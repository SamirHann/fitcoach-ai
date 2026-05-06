#!/usr/bin/env python3
"""Fonctions de calcul fitness : 1RM, TDEE, macros."""


ACTIVITY_FACTORS = {
    "sedentaire": 1.2,
    "leger": 1.375,
    "modere": 1.55,
    "actif": 1.725,
    "tres_actif": 1.9,
}


def calc_1rm(weight_kg: float, reps: int) -> float:
    """Formule d'Epley : weight * (1 + reps / 30)."""
    return round(weight_kg * (1 + reps / 30), 1)


def calc_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "modere",
) -> float:
    """Harris-Benedict révisé × facteur d'activité.

    gender : 'homme' ou 'femme'
    activity_level : sedentaire | leger | modere | actif | tres_actif
    """
    if gender.lower() in ("homme", "h", "male", "m"):
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    factor = ACTIVITY_FACTORS.get(activity_level.lower(), 1.55)
    return round(bmr * factor, 0)


def calc_macros(tdee: float, goal: str, weight_kg: float = 80.0) -> dict:
    """Calcule les macros selon l'objectif.

    goal : 'prise' | 'seche' | 'maintien'
    Retourne {'calories', 'proteines_g', 'glucides_g', 'lipides_g'}
    """
    goal = goal.lower()

    if goal == "prise":
        calories = tdee + 300
        proteines_g = round(weight_kg * 2.0, 0)
    elif goal == "seche":
        calories = tdee - 400
        proteines_g = round(weight_kg * 2.2, 0)
    else:
        calories = tdee
        proteines_g = round(weight_kg * 1.8, 0)

    lipides_g = round((calories * 0.25) / 9, 0)
    glucides_g = round((calories - (proteines_g * 4) - (lipides_g * 9)) / 4, 0)

    return {
        "calories": int(calories),
        "proteines_g": int(proteines_g),
        "glucides_g": int(max(glucides_g, 0)),
        "lipides_g": int(lipides_g),
    }


def format_1rm(weight_kg: float, reps: int) -> str:
    result = calc_1rm(weight_kg, reps)
    return (
        f"1RM estimé (formule Epley) : {result} kg\n"
        f"  → Basé sur {weight_kg} kg × {reps} répétitions"
    )


def format_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "modere",
) -> str:
    tdee = calc_tdee(weight_kg, height_cm, age, gender, activity_level)
    return (
        f"TDEE (dépense énergétique journalière) : {int(tdee)} kcal/jour\n"
        f"  → {weight_kg} kg | {height_cm} cm | {age} ans | {gender} | activité: {activity_level}"
    )


def format_macros(tdee: float, goal: str, weight_kg: float = 80.0) -> str:
    m = calc_macros(tdee, goal, weight_kg)
    return (
        f"Macros pour objectif '{goal}' ({m['calories']} kcal/jour) :\n"
        f"  Protéines : {m['proteines_g']} g\n"
        f"  Glucides  : {m['glucides_g']} g\n"
        f"  Lipides   : {m['lipides_g']} g"
    )
