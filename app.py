import streamlit as st
import pandas as pd
import json
from connectors import CONNECTORS
from schema_inferrer import infer_schema
from visualizer import build_tree_figure, build_security_gauge
from security_auditor import run_audit
from exporter import (
    export_security_report_json,
    export_security_report_csv,
    export_security_report_pdf
)
from chatbot import render_chatbot


class SafeJSONEncoder(json.JSONEncoder):
    """Encoder JSON qui convertit les types non-sérialisables en string."""
    def default(self, obj):
        import datetime
        try:
            from bson import ObjectId
            if isinstance(obj, ObjectId):
                return str(obj)
        except ImportError:
            pass
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return str(obj)

st.set_page_config(page_title="NoSQL Schema Inspector", layout="wide")

# ══════════════════════════════════════════════════════
#  PREMIUM CSS — animations + glassmorphism + SaaS style
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─── Keyframes ─────────────────────────────────── */
@keyframes fadeInUp   { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeIn     { from { opacity:0; } to { opacity:1; } }
@keyframes slideInLeft{ from { opacity:0; transform:translateX(-30px); } to { opacity:1; transform:translateX(0); } }
@keyframes gradientBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
@keyframes pulse      { 0%,100%{ box-shadow:0 0 0 0 rgba(99,102,241,.4); } 50%{ box-shadow:0 0 0 8px rgba(99,102,241,0); } }
@keyframes shimmer    { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
@keyframes glow       { 0%,100%{ text-shadow:0 0 8px rgba(139,92,246,.6); } 50%{ text-shadow:0 0 20px rgba(139,92,246,1),0 0 40px rgba(99,102,241,.5); } }

/* ─── Global ─────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1040 30%, #0f172a 60%, #0c1526 100%) !important;
    background-size: 400% 400% !important;
    animation: gradientBG 18s ease infinite !important;
    color: #e2e8f0 !important;
}

/* ─── Main content animation ─────────────────────── */
.main .block-container {
    animation: fadeInUp 0.6s ease both;
    padding-top: 0 !important;
}

/* ─── Sidebar glassmorphism ───────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.75) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(139,92,246,0.25) !important;
    box-shadow: 4px 0 30px rgba(0,0,0,0.4) !important;
    animation: slideInLeft 0.5s ease both !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* ─── Sidebar inputs ─────────────────────────────── */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(139,92,246,0.3) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.2), 0 0 12px rgba(139,92,246,0.15) !important;
    background: rgba(255,255,255,0.08) !important;
}

/* ─── Primary Button ─────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%) !important;
    background-size: 200% 200% !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.02em !important;
    padding: 12px 22px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
    animation: pulse 2.5s infinite !important;
}
.stButton > button:hover {
    background-position: right center !important;
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 25px rgba(139,92,246,0.55) !important;
    animation: none !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.99) !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
}

/* ─── Download Button ────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: rgba(255,255,255,0.04) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(139,92,246,0.35) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
    animation: none !important;
    box-shadow: none !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(139,92,246,0.12) !important;
    border-color: #8b5cf6 !important;
    color: #c4b5fd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(139,92,246,0.2) !important;
}

/* ─── Metric cards ───────────────────────────────── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    animation: fadeInUp 0.7s ease both !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 30px rgba(139,92,246,0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 32px !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
}

/* ─── Tabs ───────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-bottom: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 4px 8px 0 !important;
    gap: 4px !important;
    backdrop-filter: blur(10px) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.25s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #a5b4fc !important;
    border-bottom: 2px solid #8b5cf6 !important;
    background: rgba(139,92,246,0.1) !important;
    text-shadow: 0 0 10px rgba(139,92,246,0.5) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: #c4b5fd !important;
    background: rgba(139,92,246,0.07) !important;
}
[data-testid="stTabPanel"] {
    background: transparent !important;
    animation: fadeIn 0.4s ease both !important;
    padding-top: 20px !important;
}

/* ─── Divider ─────────────────────────────────────── */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.4), transparent) !important;
    margin: 24px 0 !important;
}

/* ─── Headers ─────────────────────────────────────── */
h1,h2,h3 { color: #f1f5f9 !important; letter-spacing: -0.02em !important; font-weight: 700 !important; }
h2 { font-size: 20px !important; }
h3 { font-size: 16px !important; }

/* ─── Alerts ─────────────────────────────────────── */
[data-testid="stAlert"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    border-left-width: 3px !important;
    backdrop-filter: blur(8px) !important;
    font-size: 13px !important;
    color: #cbd5e1 !important;
    animation: fadeIn 0.4s ease !important;
}

/* ─── Dataframe ───────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
}

/* ─── Expander ────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(10px) !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(139,92,246,0.4) !important;
}
[data-testid="stExpander"] summary { color: #94a3b8 !important; font-size: 13px !important; }

/* ─── Selectbox / Inputs ──────────────────────────── */
[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(139,92,246,0.3) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}
[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(139,92,246,0.3) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

/* ─── Multiselect tags ────────────────────────────── */
[data-baseweb="tag"] {
    background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    border-radius: 6px !important;
    font-size: 12px !important;
}
[data-baseweb="multi-select"] {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(139,92,246,0.3) !important;
    border-radius: 8px !important;
}

/* ─── Spinner ─────────────────────────────────────── */
[data-testid="stSpinner"] > div { border-top-color: #8b5cf6 !important; }

/* ─── Scrollbar ───────────────────────────────────── */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(139,92,246,0.4); border-radius:10px; }
::-webkit-scrollbar-thumb:hover { background:rgba(139,92,246,0.7); }
</style>
""", unsafe_allow_html=True)

# ── HEADER ANIMÉ ────────────────────────────────────
st.markdown("""
<div style="
    padding: 32px 0 22px 0;
    margin-bottom: 24px;
    border-bottom: 1px solid rgba(139,92,246,0.25);
    animation: fadeInUp 0.5s ease both;
">
    <div style="display:flex; align-items:center; gap:16px;">
        <div style="
            background: linear-gradient(135deg,#6366f1,#a855f7);
            border-radius: 14px;
            width: 52px; height: 52px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 6px 20px rgba(99,102,241,0.45), 0 0 40px rgba(139,92,246,0.2);
        "><svg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><ellipse cx='12' cy='5' rx='9' ry='3'/><path d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'/><path d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'/></svg></div>
        <div>
            <h1 style="
                margin:0;
                font-size:28px;
                font-weight:800;
                letter-spacing:-0.03em;
                background: linear-gradient(135deg,#e0e7ff,#c4b5fd,#a5b4fc);
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
            ">NoSQL Schema Inspector</h1>
            <p style="margin:4px 0 0;font-size:13px;color:#64748b;font-weight:400;">
                Inspection · Visualisation · Audit de sécurité des bases NoSQL
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────
st.sidebar.header("Configuration")


db_type = st.sidebar.selectbox(
    "Type de base de données",
    list(CONNECTORS.keys())
)

st.sidebar.subheader("Paramètres de connexion")

conn_params = {}

if db_type == "MongoDB":
    conn_params["uri"] = st.sidebar.text_input("URI", value="mongodb://localhost:27017")
    db_name = st.sidebar.text_input("Nom de la base", value="nosql_test")

elif db_type == "CouchDB":
    conn_params["url"] = st.sidebar.text_input("URL", value="http://localhost:5984")
    conn_params["username"] = st.sidebar.text_input("Utilisateur", value="admin")
    conn_params["password"] = st.sidebar.text_input("Mot de passe", type="password")
    db_name = ""  # CouchDB : pas de db_name, les bases sont les collections

elif db_type == "Firebase Firestore":
    st.sidebar.info(
        "Si GOOGLE_APPLICATION_CREDENTIALS est configuré, laisse tout vide "
        "et clique directement sur Connecter."
    )
    conn_params["credentials_path"] = st.sidebar.text_input(
        "Chemin serviceAccountKey.json (optionnel)",
        value="",
        placeholder="/chemin/vers/serviceAccountKey.json"
    )
    st.sidebar.markdown("*— ou renseigne les champs manuellement —*")
    fb_project_id   = st.sidebar.text_input("Project ID", placeholder="mon-projet-firebase")
    fb_client_email = st.sidebar.text_input(
        "Client Email",
        placeholder="firebase-adminsdk-xxx@mon-projet.iam.gserviceaccount.com"
    )
    fb_private_key  = st.sidebar.text_area(
        "Private Key",
        placeholder="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
        height=120
    )
    if fb_project_id and fb_client_email and fb_private_key:
        conn_params["credentials_dict"] = {
            "type": "service_account",
            "project_id": fb_project_id,
            "private_key": fb_private_key.replace("\\n", "\n"),
            "client_email": fb_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    else:
        conn_params["credentials_dict"] = None
    db_name = ""

limit = st.sidebar.number_input("Limite de documents (0 = tous)", min_value=0, value=0)

# ── CONNEXION + ANALYSE EN UN SEUL BOUTON ─────────────
if st.sidebar.button("Connecter et analyser"):
    # Vider tout l'état de la connexion précédente
    for _key in ["connector", "collections", "db_name", "db_type",
                 "limit", "selected_collections", "analyser_clicked"]:
        st.session_state.pop(_key, None)
    # Vider les caches de documents (clés "docs_*")
    for _key in [k for k in st.session_state if k.startswith("docs_")]:
        del st.session_state[_key]

    connector = CONNECTORS[db_type]()
    success = connector.connect(**conn_params)

    if not success:
        st.sidebar.error(f"Impossible de se connecter à {db_type}")
    else:
        st.sidebar.success(f"Connecté à {db_type}")
        collections = connector.get_collections(db_name)

        if not collections:
            st.sidebar.warning("Aucune collection trouvée.")
        else:
            selected = collections
            st.session_state["connector"] = connector
            st.session_state["collections"] = collections
            st.session_state["db_name"] = db_name
            st.session_state["db_type"] = db_type
            st.session_state["limit"] = limit
            st.session_state["selected_collections"] = selected
            st.session_state["analyser_clicked"] = True

# ── SÉLECTION MANUELLE DES COLLECTIONS (après connexion) ──
# N'afficher le filtre QUE si la base sélectionnée correspond à la connexion active
if (
    "collections" in st.session_state
    and st.session_state["collections"]
    and st.session_state.get("db_type") == db_type
):
    collections = st.session_state["collections"]
    current_db_type = st.session_state["db_type"]

    if current_db_type == "CouchDB":
        label_choisir = "Filtrer les bases à analyser"
    else:
        label_choisir = "Filtrer les collections à analyser"

    selected_filtered = st.sidebar.multiselect(
        label_choisir,
        collections,
        default=st.session_state.get("selected_collections", collections[:3])
    )

    if st.sidebar.button("Appliquer la sélection"):
        st.session_state["selected_collections"] = selected_filtered
        st.session_state["analyser_clicked"] = True
        for _c in selected_filtered:
            st.session_state.pop(f"docs_{_c}", None)

# ── ANALYSE ET AFFICHAGE ──────────────────────────────
if st.session_state.get("analyser_clicked") and "selected_collections" in st.session_state:
    connector = st.session_state["connector"]
    db_name = st.session_state["db_name"]
    limit = st.session_state["limit"]
    selected = st.session_state["selected_collections"]

    if not selected:
        st.warning("Veuillez sélectionner au moins une collection.")
    else:
        tabs = st.tabs(selected)

        for tab, coll_name in zip(tabs, selected):
            with tab:
                # ── FETCH DOCS (avec cache par collection) ──────────────
                _cache_key = f"docs_{coll_name}"
                if _cache_key not in st.session_state:
                    with st.spinner(f"Chargement des données de {coll_name}..."):
                        _fresh = connector.get_documents(
                            db_name, coll_name,
                            limit=limit if limit > 0 else None
                        )
                    st.session_state[_cache_key] = _fresh

                docs = st.session_state[_cache_key]

                if not docs:
                    st.warning(f"Aucun document trouvé dans '{coll_name}'.")
                    continue

                schema = infer_schema(docs)

                if not schema:
                    st.warning(f"Schéma vide pour '{coll_name}'.")
                    continue

                # ── EN-TÊTE : titre + bouton Actualiser (top-right) ───────
                col_title, col_btn = st.columns([8, 2])
                with col_title:
                    st.markdown(
                        f"<span style='font-size:13px;color:#6b7280'>"
                        f"Collection : <b style='color:#1e3a5f'>{coll_name}</b></span>",
                        unsafe_allow_html=True
                    )
                with col_btn:
                    if st.button(
                        "\u21bb  Actualiser",
                        key=f"reload_{coll_name}",
                        help="Re-récupérer les données depuis la base de données",
                        use_container_width=True
                    ):
                        # Supprimer le cache de CETTE collection uniquement
                        st.session_state.pop(f"docs_{coll_name}", None)

                st.divider()

                # ── MÉTRIQUES GLOBALES ────────────────────────
                col1, col2, col3 = st.columns(3)
                col1.metric("Documents analysés", len(docs))
                col2.metric("Champs détectés", len(schema))
                col3.metric("Champs à 100%", sum(
                    1 for f in schema.values() if f["presence"] == 100.0
                ))

                st.divider()

                # ── SOUS-ONGLETS ──────────────────────────────
                schema_tab, security_tab = st.tabs(
                    ["Schema & Visualisation", "Audit Securite"]
                )

                # ═══════════════════════════════════════════════
                # TAB 1 — SCHÉMA
                # ═══════════════════════════════════════════════
                with schema_tab:
                    st.subheader("Schéma découvert")
                    rows = [
                        {
                            "Champ": field,
                            "Type(s)": ", ".join(
                                f"{t}({n}x)" for t, n in info["types"].items()
                            ),
                            "Présence (%)": info["presence"],
                            "Occurrences": info["count"]
                        }
                        for field, info in sorted(schema.items())
                    ]
                    df = pd.DataFrame(rows)

                    def color_presence(val):
                        if val == 100.0:
                            return "background-color: #166534; color: white"
                        elif val >= 50:
                            return "background-color: #854d0e; color: white"
                        else:
                            return "background-color: #7f1d1d; color: white"

                    dynamic_height = min(400, max(100, len(df) * 35 + 40))
                    styled_df = df.style.map(color_presence, subset=["Présence (%)"])
                    st.dataframe(
                        styled_df, width="stretch", height=dynamic_height
                    )

                    st.divider()
                    st.subheader("Schéma visuel")
                    st.markdown("""
                    *Guide des couleurs :*
                    🟢 100% des documents &nbsp;|&nbsp;
                    🔵 +50% &nbsp;|&nbsp;
                    ⚫ Rare (-50%) &nbsp;|&nbsp;
                    🟠 Type mixte
                    """)
                    fig = build_tree_figure(schema, collection_name=coll_name)
                    st.plotly_chart(
                        fig, width="stretch", key=f"chart_{coll_name}"
                    )

                    st.divider()
                    st.subheader("Exporter le schéma")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button(
                            "Telecharger JSON (schema)",
                            json.dumps(schema, indent=2, ensure_ascii=False, cls=SafeJSONEncoder),
                            file_name=f"schema_{coll_name}.json",
                            mime="application/json",
                            key=f"json_{coll_name}"
                        )
                    with col_b:
                        st.download_button(
                            "Telecharger CSV (schema)",
                            df.to_csv(index=False).encode("utf-8"),
                            file_name=f"schema_{coll_name}.csv",
                            mime="text/csv",
                            key=f"csv_{coll_name}"
                        )

                    with st.expander("Voir les documents bruts"):
                        st.json(docs[:5])

                # ═══════════════════════════════════════════════
                # TAB 2 — AUDIT SÉCURITÉ
                # ═══════════════════════════════════════════════
                with security_tab:
                    with st.spinner("Analyse des vulnérabilités..."):
                        audit = run_audit(docs, schema)

                    score   = audit["score"]
                    summary = audit["summary"]
                    findings = audit["findings"]

                    # ── Jauge + résumé ───────────────────────
                    col_gauge, col_cards = st.columns([2, 3])

                    with col_gauge:
                        fig_gauge = build_security_gauge(score)
                        st.plotly_chart(
                            fig_gauge, width="stretch",
                            key=f"gauge_{coll_name}"
                        )

                    with col_cards:
                        st.markdown("#### Résumé des findings")
                        sev_cfg = [
                            ("CRITICAL", "🔴", "#dc2626", "#450a0a"),
                            ("HIGH",     "🟠", "#ea580c", "#431407"),
                            ("MEDIUM",   "🟡", "#ca8a04", "#422006"),
                            ("INFO",     "🔵", "#2563eb", "#1e3a5f"),
                        ]
                        for sev, icon, fg, bg in sev_cfg:
                            count = summary.get(sev, 0)
                            st.markdown(
                                f"""
                                <div style="
                                    background:{bg};
                                    border-left: 4px solid {fg};
                                    padding: 10px 16px;
                                    border-radius: 6px;
                                    margin-bottom: 8px;
                                    color:white;
                                    font-size: 15px;
                                ">
                                {icon} <b>{sev}</b> — {count} finding(s)
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    st.divider()

                    # ── Détail des findings ──────────────────
                    if not findings:
                        st.success(
                            "Aucune vulnérabilité détectée dans cette collection !"
                        )
                    else:
                        st.subheader("Détail des vulnérabilités")

                        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
                        sorted_findings = sorted(
                            findings,
                            key=lambda x: sev_order.get(x["severity"], 99)
                        )

                        sev_colors = {
                            "CRITICAL": ("#dc2626", "#450a0a", "🔴"),
                            "HIGH":     ("#ea580c", "#431407", "🟠"),
                            "MEDIUM":   ("#ca8a04", "#422006", "🟡"),
                            "INFO":     ("#2563eb", "#1e3a5f", "🔵"),
                        }

                        for f in sorted_findings:
                            fg, bg, icon = sev_colors.get(
                                f["severity"], ("#6b7280", "#1f2937", "•")
                            )
                            st.markdown(
                                f"""
                                <div style="
                                    background:{bg};
                                    border-left:5px solid {fg};
                                    padding:12px 18px;
                                    border-radius:8px;
                                    margin-bottom:10px;
                                    color:white;
                                ">
                                <div style="font-size:14px;font-weight:bold;margin-bottom:4px">
                                    {icon} [{f['severity']}] &nbsp;
                                    <code style="color:{fg}">{f['rule']}</code>
                                    &nbsp;—&nbsp; champ : <b>{f['field']}</b>
                                </div>
                                <div style="font-size:13px;margin-bottom:4px">{f['message']}</div>
                                <div style="font-size:12px;opacity:0.8">
                                    📄 Documents touchés : <b>{f['affected_docs']}</b>
                                    &nbsp;|&nbsp; Exemple (masqué) :
                                    <code>{f['sample']}</code>
                                </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    st.divider()

                    # ── Export du rapport ────────────────────────
                    st.subheader("Exporter le rapport de sécurité")
                    col_rj, col_rc, col_rp = st.columns(3)

                    with col_rj:
                        st.download_button(
                            "Telecharger JSON (rapport)",
                            export_security_report_json(audit, coll_name),
                            file_name=f"security_{coll_name}.json",
                            mime="application/json",
                            key=f"sec_json_{coll_name}"
                        )
                    with col_rc:
                        st.download_button(
                            "Telecharger CSV (rapport)",
                            export_security_report_csv(audit),
                            file_name=f"security_{coll_name}.csv",
                            mime="text/csv",
                            key=f"sec_csv_{coll_name}"
                        )
                    with col_rp:
                        try:
                            pdf_bytes = export_security_report_pdf(audit, coll_name)
                            st.download_button(
                                "Telecharger PDF (rapport)",
                                pdf_bytes,
                                file_name=f"security_{coll_name}.pdf",
                                mime="application/pdf",
                                key=f"sec_pdf_{coll_name}"
                            )
                        except ImportError:
                            st.warning(
                                "Export PDF indisponible : "
                                "installez reportlab (pip install reportlab)"
                            )

# ── FLOATING CHATBOT (always rendered last) ───────────────────────────────────
render_chatbot()
