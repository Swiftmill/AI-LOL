# AI Locale

Assistant web local en FastAPI avec mémoire de fichiers JSON.

## Fonctionnalités
- Compréhension de texte via spaCy + Sentence Transformers.
- Alias, règles et faits persistés en JSON/JSONL.
- Recherche web (DuckDuckGo) avec résumé TextRank.
- Interface web sombre responsive servie par FastAPI.
- Journalisation JSONL et index TF-IDF pour les faits appris.

## Prérequis
- Python 3.11+
- Accès internet pour la première installation des dépendances et modèles spaCy.

## Installation
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m spacy download fr_core_news_sm
python -m spacy download en_core_web_sm
```

## Lancement
```bash
python app.py
```
L'interface est disponible sur http://127.0.0.1:8000/.

## Tests d'acceptation rapides
1. Envoyez `bonjour` → la règle répond « salut mec ».
2. Envoyez `Rblx ça veut dire Roblox` → l'IA confirme l'alias.
3. Demandez `c'est quoi rblx ?` avec l'option web désactivée → propose une recherche.
4. Reposez la question avec recherche activée → l'IA apprend, répond et mémorise les sources.

## Construction .exe (Windows)
```bat
call tools\pack_win.bat
```
Le binaire se trouvera dans `dist\MyLocalAI.exe`.

## Structure
```
ai-local/
  app.py
  core/
    nlu.py
    ontology.py
    rules.py
    facts.py
    search.py
    summarize.py
    index.py
    pipeline.py
    store.py
  ui/
    index.html
    script.js
    styles.css
  data/
    rules.jsonl
    facts.jsonl
    ontology/aliases.json
    pages/
    index.json
    memory/profile.json
    logs/
  tools/pack_win.bat
  requirements.txt
  README.md
```

