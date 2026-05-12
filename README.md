# NoSQL Schema Inspector

**NoSQL Schema Inspector** est une application web professionnelle construite avec **Streamlit**. Elle permet de se connecter à vos bases de données NoSQL (MongoDB, CouchDB, Firebase Firestore), d'inférer dynamiquement leurs schémas cachés, de les visualiser, et de réaliser un audit de sécurité automatisé.

![NoSQL Schema Inspector](images/favicon.png)

## Fonctionnalités Principales

- **Inférence de Schéma** : Détection automatique des champs, types, et pourcentages de présence.
- **Visualisation** : Cartographie visuelle du schéma avec `Plotly` (Treemaps).
- **Audit de Sécurité** : Détection de vulnérabilités (mots de passe en clair, PII exposées, risques d'injection NoSQL, tokens, etc.) avec calcul d'un score de sécurité.
- **Export** : Génération de rapports en JSON, CSV et PDF.
- **Assistant IA Intégré** : Un chatbot propulsé par Groq (LLaMA 3) pour vous guider.
- **Connecteurs Multiples** : Supporte MongoDB, CouchDB, et Firestore par défaut. Extensible à d'autres moteurs NoSQL.

## Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/hibasb/NoSQL_Schema_inspector.git
   cd NoSQL_Schema_inspector
   ```

2. Créez un environnement virtuel et installez les dépendances :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sous Windows : venv\Scripts\activate
   pip install -r requirements.txt
   ```
   *(Assurez-vous d'avoir installé les packages comme `streamlit`, `pymongo`, `firebase-admin`, `requests`, `plotly`, `reportlab`,
   `groq`, `python-dotenv`)*

3. Configuration :
   Copiez le fichier d'exemple des variables d'environnement et ajoutez votre clé API Groq pour activer le chatbot IA :
   ```bash
   cp .env.example .env
   ```

## Utilisation

Lancez l'application Streamlit :
```bash
streamlit run app.py
```
L'interface s'ouvrira automatiquement dans votre navigateur (généralement à l'adresse `http://localhost:8501`).

## Structure du Projet

- `app.py` : L'interface principale Streamlit.
- `connectors/` : Les classes de connexion pour MongoDB, CouchDB, Firestore.
- `schema_inferrer.py` : La logique d'analyse et de détection des types.
- `security_auditor.py` : Le moteur d'évaluation des risques et règles de sécurité.
- `visualizer.py` : La génération des graphiques Plotly.
- `exporter.py` : La logique de téléchargement des rapports (JSON, CSV, PDF).
- `chatbot.py` : L'intégration du widget assistant IA.

