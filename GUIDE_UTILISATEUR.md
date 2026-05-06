# Guide Utilisateur — FitCoach AI

## C'est quoi FitCoach AI ?

FitCoach AI est un assistant intelligent spécialisé en musculation. Contrairement à un chatbot généraliste, il répond à partir de **vrais documents** (programmes, guides nutritionnels) et peut **calculer des données personnalisées** comme ton 1RM, ton TDEE ou tes macros.

Il fonctionne entièrement en local — aucune donnée n'est envoyée sur internet.

---

## Lancer l'assistant

```bash
docker compose run -it app python src/main.py
```

Tu verras apparaître :

```
╔══════════════════════════════════════════╗
║           FitCoach AI  🏋️               ║
║  Assistant musculation multi-agents      ║
╚══════════════════════════════════════════╝
Commandes : 'exit' pour quitter | 'clear' pour vider la mémoire

Vous: _
```

Tape ta question et appuie sur Entrée.

---

## Ce que l'IA peut faire

### 0. Conversation naturelle
L'IA comprend les messages conversationnels et y répond directement, sans chercher dans les documents fitness.

**Exemples :**
```
Bonjour !
Comment tu vas ?
C'est quoi ton rôle ?
Merci !
```

**Ce que tu verras :**
```
[Routeur] → Agent choisi : Chat

[Final] → Bonjour ! Je suis FitCoach AI, ton assistant musculation.
Pose-moi une question sur l'entraînement, la nutrition ou demande-moi
un calcul (1RM, TDEE, macros) !
```

> **Note :** Le routeur utilise le LLM pour décider quel agent appeler. Cela ajoute quelques secondes de traitement pour chaque message, y compris les salutations.

---

### 1. Répondre à tes questions sur l'entraînement
L'IA consulte les documents chargés dans sa base (programmes PPL, guides, etc.) et te donne une réponse **sourcée avec citations précises**.

**Exemples de questions :**
```
Quels exercices pour les pectoraux en PPL ?
Combien de séries par semaine pour le dos ?
Quelle est la différence entre un Rowing barre et un Tirage poulie ?
Comment progresser en squat ?
À quelle fréquence travailler les biceps ?
```

**Ce que tu verras dans la console :**
```
[Routeur] → Agent choisi : RAG
[RAG] → Documents consultés :
        exemple_programme.txt, chunk_2
        exemple_programme.txt, chunk_7

[Final] → En programme PPL, les pectoraux sont travaillés 2 fois par semaine :
Jour 1 (Push lourd) avec développé couché, dips et développé incliné,
et Jour 4 (Push léger) avec des exercices d'isolation.
[Source: exemple_programme.txt, chunk 2]
```

---

### 2. Calculer ton 1RM (charge maximale)

Le 1RM (One Rep Max) est la charge maximale que tu peux soulever une seule fois. L'IA utilise la **formule d'Epley** pour l'estimer à partir d'une série sous-maximale.

**Formule :** `1RM = poids × (1 + reps / 30)`

**Exemples de questions :**
```
Calcule mon 1RM : 80kg x 8 reps
Mon 1RM au développé couché : 100kg pour 5 reps
Quel est mon 1RM si je fais 60kg × 12 répétitions ?
```

**Résultat attendu :**
```
[Routeur] → Agent choisi : Tools
[Outil] → calculator appelé
         Résultat brut : 1RM estimé (formule Epley) : 106.7 kg

[Final] → Ton 1RM estimé est de 106.7 kg, basé sur 80 kg × 8 répétitions.
```

---

### 3. Calculer ton TDEE (calories journalières)

Le TDEE (Total Daily Energy Expenditure) est le nombre de calories que ton corps brûle par jour en tenant compte de ton activité physique.

**Informations nécessaires :** poids (kg), taille (cm), âge, sexe, niveau d'activité

**Niveaux d'activité disponibles :**
| Niveau | Description |
|--------|-------------|
| `sédentaire` | Bureau, peu ou pas de sport |
| `léger` | Sport 1-3 fois par semaine |
| `modéré` | Sport 3-5 fois par semaine |
| `actif` | Sport intense 6-7 fois par semaine |
| `très actif` | Athlète, travail physique intense |

**Exemples de questions :**
```
Mon TDEE : 75kg, 175cm, 25 ans, homme, modérément actif
Calcule mon TDEE pour une femme de 60kg, 165cm, 30 ans, active
Combien de calories je brûle par jour ? 85kg, 180cm, 22 ans, homme, actif
```

**Résultat attendu :**
```
[Routeur] → Agent choisi : Tools
[Outil] → calculator appelé

[Final] → Ton TDEE est estimé à 2 893 kcal/jour.
Basé sur : 75 kg | 175 cm | 25 ans | homme | activité : modéré
```

---

### 4. Calculer tes macros (protéines, glucides, lipides)

L'IA calcule la répartition idéale de tes macronutriments selon ton objectif.

**Objectifs disponibles :**
- `prise` (prise de masse) — surplus de +300 kcal, protéines à 2g/kg
- `sèche` (perte de gras) — déficit de -400 kcal, protéines à 2,2g/kg
- `maintien` — calories = TDEE, protéines à 1,8g/kg

**Exemples de questions :**
```
Calcule mes macros pour une prise de masse : 80kg, 2800 kcal
Mes macros pour une sèche : 75kg, 2500 kcal
Donne-moi mes macros en maintien pour 70kg et 2200 kcal
```

**Résultat attendu :**
```
[Routeur] → Agent choisi : Tools
[Outil] → calculator appelé

[Final] → Macros pour objectif 'prise' (3 100 kcal/jour) :
  Protéines : 160 g
  Glucides  : 400 g
  Lipides   : 86 g
```

---

### 5. Chercher des études et informations récentes

L'IA peut effectuer une recherche web (DuckDuckGo) pour trouver des études ou informations récentes sur la musculation.

**Exemples de questions :**
```
Cherche des études récentes sur la créatine
Quelles sont les dernières recherches sur le volume d'entraînement ?
Recherche des infos sur la supplémentation en oméga-3 et la récupération
```

---

## La mémoire conversationnelle

L'IA se souvient de tes **3 dernières questions et réponses**. Tu peux donc enchaîner les échanges sans répéter le contexte.

**Exemple :**
```
Vous: Calcule mon 1RM : 100kg x 5 reps

[Final] → Ton 1RM estimé est de 116.7 kg.

---

Vous: Et si je fais 90kg x 8 reps ?

[Final] → Pour 90 kg × 8 répétitions, ton 1RM estimé est de 114 kg.
(légèrement inférieur à ton précédent calcul de 116.7 kg)

---

Vous: Peux-tu m'expliquer comment utiliser ces résultats ?

[Final] → En te basant sur tes 1RM (116.7 kg et 114 kg), tu peux
structurer tes charges d'entraînement ainsi : ...
```

**Vider la mémoire :** tape `clear` pour repartir d'une conversation propre.

---

## Commandes disponibles

| Commande | Action |
|----------|--------|
| Ta question | L'IA répond |
| `clear` | Efface les 3 derniers échanges mémorisés |
| `exit` | Quitter FitCoach AI |
| `Ctrl+C` | Quitter (urgence) |

---

## Ce que l'IA ne fait PAS

- **Elle ne donne pas de conseils médicaux.** Pour tout problème de santé, consulte un médecin.
- **Elle ne répond qu'aux questions liées à la musculation et la nutrition sportive.** Les questions hors sujet (météo, économie, etc.) seront poliment refusées.
- **Elle ne mémorise pas entre deux sessions.** La mémoire est remise à zéro à chaque redémarrage du programme.
- **Elle ne connaît que les documents chargés.** Si un document n'a pas été ingéré, elle ne pourra pas en citer le contenu.

---

## Lire les infos système

La console affiche toujours dans cet ordre ce qui se passe en coulisses :

```
[Routeur] → Agent choisi : RAG          ← quel agent a été sélectionné
[RAG] → Documents consultés : ...       ← quels passages ont été trouvés (si RAG)
[Outil] → calculator appelé : ...       ← quel outil a été utilisé (si Tools)
[Final] → ta réponse                    ← la réponse finale
```

Cela te permet de comprendre **pourquoi** l'IA te donne cette réponse et de vérifier les sources.

---

## Ajouter tes propres documents

1. Copie ton fichier PDF ou TXT dans le dossier `docs/`
2. Relance l'ingestion :
   ```bash
   docker compose run --rm app python src/ingest.py
   ```
3. L'IA pourra désormais citer ton document dans ses réponses.

---

## Dépannage

| Problème | Solution |
|----------|----------|
| "Connexion refusée à ChromaDB" | `docker compose up -d chromadb` |
| "Ollama ne répond pas" | `docker compose up -d ollama` puis attendre 30 secondes |
| "Aucun résultat RAG" | Vérifier que `src/ingest.py` a bien été lancé |
| L'IA répond en anglais | Ajouter "Réponds en français s'il te plaît" à ta question |
| Réponse très lente | Normal pour la première requête (chargement du modèle Ollama) |

---

*FitCoach AI — Ce système est un outil d'aide et ne remplace pas l'accompagnement d'un coach certifié ou d'un médecin du sport.*
