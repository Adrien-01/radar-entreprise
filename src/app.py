import streamlit as st
import duckdb
from src.ingestion.fetch_api import ingest_siren_data_to_duckdb
from src.components.company_info import afficher_fiche_identite
from src.components.kpi_cards import render_kpi_cards

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Radar Entreprise - Analyse & Veille",
    page_icon="🏢",
    layout="wide"
)

# Injection de styles CSS personnalisés pour les badges et cartes KPI
st.markdown("""
    <style>
    .kpi-card-large {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .kpi-title {
        font-size: 14px;
        color: #6c757d;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .kpi-body {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .kpi-value-large {
        font-size: 28px;
        font-weight: 700;
        color: #212529;
    }
    .kpi-unit-large {
        font-size: 14px;
        color: #6c757d;
    }
    .kpi-footer {
        font-size: 11px;
        color: #adb5bd;
        margin-top: 12px;
        border-top: 1px solid #e9ecef;
        padding-top: 8px;
    }
    .badge-dark {
        background-color: #212529;
        color: #fff;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-red {
        background-color: #dc3545;
        color: #fff;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Initialisation de la connexion DuckDB en mémoire
@st.cache_resource
def get_duckdb_connection():
    return duckdb.connect(":memory:")

conn = get_duckdb_connection()

# En-tête de l'application
st.title("radar-entreprise 📊")
st.markdown("Plateforme de veille et d'analyse financière et légale des entreprises (données officielles en temps réel).")

# Barre latérale (Sidebar) pour la recherche par SIREN
st.sidebar.header("🔍 Recherche d'entreprise")
siren_input = st.sidebar.text_input("Numéro SIREN (9 chiffres)", value="424761419")
search_button = st.sidebar.button("Analyser l'entreprise")

# Logique exécutée lors de la recherche
if search_button or siren_input:
    siren_cleaned = siren_input.strip()

    if len(siren_cleaned) != 9 or not siren_cleaned.isdigit():
        st.error("Veuillez saisir un numéro SIREN valide comportant exactement 9 chiffres.")
    else:
        with st.spinner(f"Interrogation des API officielles pour le SIREN {siren_cleaned}..."):
            try:
                # 1. Ingestion des données réelles dans DuckDB
                ingest_siren_data_to_duckdb(siren_cleaned, conn)

                # 2. Requête de fusion (JOIN) pour récupérer toutes les données unifiées
                query = """
                    SELECT
                        s.*,
                        b.flag_bodacc,
                        m.nb_marches_boamp,
                        m.profil_commande_publique
                    FROM raw_sirene s
                    LEFT JOIN raw_bodacc b ON s.siren = b.siren
                    LEFT JOIN raw_boamp m ON s.siren = m.siren
                    WHERE s.siren = ?
                """
                result = conn.execute(query, [siren_cleaned]).fetchone()

                if result:
                    columns = [desc[0] for desc in conn.description]
                    company_data = dict(zip(columns, result))

                    # Données additionnelles fictives/calculées pour les ratios de tension sectorielle (optionnel)
                    company_data["ratio_creation_fermeture"] = 1.15
                    company_data["qualification_tension"] = "Secteur dynamique"

                    # 3. Affichage des composants Streamlit
                    st.success(f"Données chargées avec succès pour : **{company_data.get('raison_sociale')}**")

                    # Fiche d'identité
                    afficher_fiche_identite(company_data)

                    st.subheader("📈 Indicateurs Clés de Performance (KPI)")
                    # Cartes KPI
                    render_kpi_cards(company_data)

                else:
                    st.warning("Aucune donnée trouvée pour ce SIREN dans la base.")

            except Exception as e:
                st.error(f"Une erreur est survenue lors de la récupération des données : {e}")
else:
    st.info("Veuillez entrer un numéro SIREN dans la barre latérale pour lancer l'analyse.")
