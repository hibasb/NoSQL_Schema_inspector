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
st.title("NoSQL Schema Inspector")
st.caption("Inspection de schéma pour bases de données orientées document")

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
    st.sidebar.info("Si GOOGLE_APPLICATION_CREDENTIALS est configuré, laisse vide.")
    conn_params["credentials_path"] = st.sidebar.text_input(
        "Chemin serviceAccountKey.json (optionnel)",
        value=""
    )
    db_name = ""

limit = st.sidebar.number_input("Limite de documents (0 = tous)", min_value=0, value=100)

# ── CONNEXION ─────────────────────────────────────────
if st.sidebar.button("Connecter"):
    connector = CONNECTORS[db_type]()
    success = connector.connect(**conn_params)

    if not success:
        st.sidebar.error(f"Impossible de se connecter à {db_type}")
    else:
        st.sidebar.success(f"Connecté à {db_type}")
        collections = connector.get_collections(db_name)
        st.session_state["connector"] = connector
        st.session_state["collections"] = collections
        st.session_state["db_name"] = db_name
        st.session_state["db_type"] = db_type
        st.session_state["limit"] = limit

# ── SÉLECTION DES COLLECTIONS ─────────────────────────
if "collections" in st.session_state and st.session_state["collections"]:
    collections = st.session_state["collections"]
    current_db_type = st.session_state["db_type"]

    if current_db_type == "CouchDB":
        label_collections = "Bases de données disponibles"
        label_choisir = "Choisir les bases à analyser"
    else:
        label_collections = "Collections disponibles"
        label_choisir = "Choisir les collections à analyser"

    st.sidebar.subheader(label_collections)
    selected = st.sidebar.multiselect(
        label_choisir,
        collections,
        default=collections[:3]
    )

    if st.sidebar.button("Analyser"):
        st.session_state["selected_collections"] = selected
        st.session_state["analyser_clicked"] = True

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
                with st.spinner(f"Analyse de {coll_name}..."):
                    docs = connector.get_documents(
                        db_name, coll_name,
                        limit=limit if limit > 0 else None
                    )

                if not docs:
                    st.warning(f"Aucun document trouvé dans '{coll_name}'.")
                    continue

                schema = infer_schema(docs)

                if not schema:
                    st.warning(f"Schéma vide pour '{coll_name}'.")
                    continue

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
                    ["📊 Schéma & Visualisation", "🔒 Audit Sécurité"]
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
                            "📥 JSON (schéma)",
                            json.dumps(schema, indent=2, ensure_ascii=False, cls=SafeJSONEncoder),
                            file_name=f"schema_{coll_name}.json",
                            mime="application/json",
                            key=f"json_{coll_name}"
                        )
                    with col_b:
                        st.download_button(
                            "📥 CSV (schéma)",
                            df.to_csv(index=False).encode("utf-8"),
                            file_name=f"schema_{coll_name}.csv",
                            mime="text/csv",
                            key=f"csv_{coll_name}"
                        )

                    with st.expander("👁️ Voir les documents bruts"):
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
                            "✅ Aucune vulnérabilité détectée dans cette collection !"
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
                            "📥 JSON (rapport)",
                            export_security_report_json(audit, coll_name),
                            file_name=f"security_{coll_name}.json",
                            mime="application/json",
                            key=f"sec_json_{coll_name}"
                        )
                    with col_rc:
                        st.download_button(
                            "📥 CSV (rapport)",
                            export_security_report_csv(audit),
                            file_name=f"security_{coll_name}.csv",
                            mime="text/csv",
                            key=f"sec_csv_{coll_name}"
                        )
                    with col_rp:
                        try:
                            pdf_bytes = export_security_report_pdf(audit, coll_name)
                            st.download_button(
                                "📥 PDF (rapport)",
                                pdf_bytes,
                                file_name=f"security_{coll_name}.pdf",
                                mime="application/pdf",
                                key=f"sec_pdf_{coll_name}"
                            )
                        except ImportError:
                            st.warning(
                                "📦 Export PDF indisponible : "
                                "installez `reportlab` (`pip install reportlab`)"
                            )