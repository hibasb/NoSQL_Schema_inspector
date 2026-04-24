import streamlit as st
import pandas as pd
import json
from connector import get_connection, get_collection, get_documents, get_collections_list
from schema_inferrer import infer_schema
from visualizer import build_tree_figure

# ── CONFIG PAGE ──────────────────────────────────────
st.set_page_config(
    page_title="NoSQL Schema Inspector",
    page_icon="images/logo.jpeg",
    layout="wide"
)

col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image("images/search_icon.png", width=60)
with col2:
    st.title("NoSQL Schema Inspector")
st.caption("Découverte automatique de la structure de vos collections MongoDB")

# ── SIDEBAR : CONNEXION ───────────────────────────────
st.sidebar.header("Connexion MongoDB")

uri = st.sidebar.text_input("URI MongoDB", value="mongodb://localhost:27017")
db_name = st.sidebar.text_input("Nom de la base", value="nosql_inspector_db")
collection_name = st.sidebar.text_input("Nom de la collection (optionnel)", value="")
limit = st.sidebar.number_input("Limite de documents (0 = tous)", min_value=0, value=0)

analyser = st.sidebar.button("Analyser")

if analyser:
    st.session_state["analyser_clicked"] = True

# ── ANALYSE ───────────────────────────────────────────
if st.session_state.get("analyser_clicked", False):
    with st.spinner("Connexion et analyse en cours..."):

        client = get_connection(uri)

        if client is None:
            st.error("Impossible de se connecter à MongoDB.")
        else:
            if collection_name.strip():
                collections_to_analyze = [collection_name.strip()]
            else:
                collections_to_analyze = get_collections_list(client, db_name)

            if not collections_to_analyze:
                st.warning("Aucune collection à analyser.")
            else:
                tabs = st.tabs(collections_to_analyze)
                
                for tab, coll_name in zip(tabs, collections_to_analyze):
                    with tab:
                        collection = get_collection(client, db_name, coll_name)
                        if collection is None:
                            st.error(f"Collection {coll_name} introuvable.")
                            continue
                            
                        documents = get_documents(collection, limit=limit if limit > 0 else None)

                        if not documents:
                            st.warning(f"Aucun document trouvé dans la collection {coll_name}.")
                        else:
                            schema = infer_schema(documents)

                            # ── MÉTRIQUES ─────────────────────────────
                            st.success(f"Analyse terminée sur {len(documents)} documents")

                            col1, col2, col3 = st.columns(3)
                            col1.metric("Documents analysés", len(documents))
                            col2.metric("Champs détectés", len(schema))

                            champs_obligatoires = sum(
                                1 for f in schema.values() if f["presence"] == 100.0
                            )
                            col3.metric("Champs présents partout", champs_obligatoires)

                            st.divider()

                            # ── TABLEAU PRINCIPAL ─────────────────────
                            st.subheader("Schéma découvert")

                            rows = []
                            for field, info in sorted(schema.items()):
                                types_str = ", ".join(
                                    f"{t} ({n}x)" for t, n in info["types"].items()
                                )
                                rows.append({
                                    "Champ": field,
                                    "Type(s)": types_str,
                                    "Présence (%)": info["presence"],
                                    "Occurrences": info["count"]
                                })

                            df = pd.DataFrame(rows, columns=["Champ", "Type(s)", "Présence (%)", "Occurrences"])

                            # Colorier selon la présence
                            def color_presence(val):
                                if val == 100.0:
                                    return "background-color: #166534; color: white"
                                elif val >= 50:
                                    return "background-color: #854d0e; color: white"
                                else:
                                    return "background-color: #7f1d1d; color: white"

                            # Calcul de la hauteur dynamique (environ 35px par ligne + 40px d'entête)
                            # Limité à 400px pour éviter que le tableau soit trop long
                            dynamic_height = min(400, max(100, len(df) * 35 + 40))

                            if not df.empty:
                                styled_df = df.style.map(
                                    color_presence, subset=["Présence (%)"]
                                )
                                st.dataframe(styled_df, use_container_width=True, height=dynamic_height)
                            else:
                                st.info("Aucun champ détecté dans ces documents (ils sont probablement vides).")
                                st.dataframe(df, use_container_width=True, height=dynamic_height)

                            st.divider()

                            # ── VISUALISATION ARBRE ───────────────────────────────
                            st.subheader("Schéma visuel interactif")

                            st.markdown("""*Guide des couleurs :*
                            🟢 Présent dans 100% des documents &nbsp;|&nbsp;
                            🔵 Présent dans +50% &nbsp;|&nbsp;
                            ⚫ Rare (-50%) &nbsp;|&nbsp;
                            🟠 Type mixte (plusieurs types détectés)
                            """)

                            fig = build_tree_figure(schema, collection_name=coll_name)
                            st.plotly_chart(fig, use_container_width=True)

                            # ── EXPORT ────────────────────────────────
                            st.subheader("Exporter le schéma")

                            col_a, col_b = st.columns(2)

                            # Export JSON
                            with col_a:
                                json_data = json.dumps(schema, indent=2, ensure_ascii=False)
                                st.download_button(
                                    label="Télécharger en JSON",
                                    data=json_data,
                                    file_name=f"schema_{coll_name}.json",
                                    mime="application/json",
                                    key=f"json_{coll_name}"
                                )

                            # Export CSV
                            with col_b:
                                csv_data = df.to_csv(index=False).encode("utf-8")
                                st.download_button(
                                    label="Télécharger en CSV",
                                    data=csv_data,
                                    file_name=f"schema_{coll_name}.csv",
                                    mime="text/csv",
                                    key=f"csv_{coll_name}"
                                )

                            # ── APERÇU DOCUMENTS BRUTS ────────────────
                            with st.expander("Voir les documents bruts"):
                                st.json(documents[:5])