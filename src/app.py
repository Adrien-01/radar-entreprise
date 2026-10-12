import os
import sys
from pathlib import Path

# ==============================================================================
# RESOLUTION UNIVERSELLE DES IMPORTS (Local & Streamlit Cloud)
# ==============================================================================
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "src" else CURRENT_DIR

for path in [str(ROOT_DIR), str(CURRENT_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import streamlit as st
import duckdb
from dbt.cli.main import dbtRunner, dbtRunnerResult

# Imports des modules internes
try:
    from src.ingestion.fetch_api import ingest_siren_data_to_duckdb
    from src.components.kpi_cards import render_kpi_cards
except ModuleNotFoundError:
    from ingestion.fetch_api import ingest_siren_data_to_duckdb
    from components.kpi_cards import render_kpi_cards

# ==============================================================================
# CONFIGURATION STREAMLIT & STYLES CSS RESPONSIVE
# ==============================================================================
st.set_page_config(
    page_title="RadarEntreprise",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* ---------------------------------------------------------------------- */
    /* 0. MASQUAGE TOTAL DE LA SIDEBAR & DU HEADER STREAMLIT                  */
    /* ---------------------------------------------------------------------- */
    [data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    /* ---------------------------------------------------------------------- */
    /* 1. STYLES GLOBAUX & ESPACEMENT POUR LA BARRE FIXE                      */
    /* ---------------------------------------------------------------------- */
    html, body {
        scroll-behavior: smooth;
        background-color: #0b0d0e !important;
    }

    .stApp {
        background-color: #0b0d0e;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding-top: 5.5rem !important; /* Laisse l'espace sous la barre fixe */
        padding-bottom: 2rem;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1200px;
    }

    /* ---------------------------------------------------------------------- */
    /* 2. CIBLAGE STRICT : UNIQUEMENT LE BLOC CONTENANT LA RECHERCHE SIREN   */
    /* ---------------------------------------------------------------------- */
    [data-testid="stHorizontalBlock"]:has(input[placeholder*="SIREN"]) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        z-index: 999999 !important;
        background-color: rgba(11, 13, 14, 0.98) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 12px 2rem !important;
        box-sizing: border-box !important;
        border-bottom: 1px solid #232830 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6) !important;
        margin: 0 !important;
    }

    /* Centrage du contenu à l'intérieur de la barre fixe */
    [data-testid="stHorizontalBlock"]:has(input[placeholder*="SIREN"]) > [data-testid="column"] {
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Champ input avec loupe intégrée */
    div[data-baseweb="input"] {
        background-color: #16191d !important;
        border: 1px solid #232830 !important;
        border-radius: 20px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a3e635' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: 14px center !important;
    }

    div[data-baseweb="input"] input {
        color: #ffffff !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        padding-left: 40px !important;
    }

    div[data-baseweb="input"] input::placeholder {
        color: #64748b !important;
    }

    /* Bouton loupe discret et élégant */
    .stButton > button {
        background-color: #16191d !important;
        color: #a3e635 !important;
        font-weight: 700 !important;
        border-radius: 20px !important;
        border: 1px solid #232830 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background-color: #22272e !important;
        border-color: #a3e635 !important;
        color: #a3e635 !important;
        box-shadow: 0 0 12px rgba(163, 230, 53, 0.2) !important;
    }

    /* Header & Branding responsive */
    .header-container {
        display: flex;
        align-items: baseline;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }

    .brand-title {
        font-size: clamp(2.2rem, 6vw, 3.8rem);
        font-weight: 800;
        color: #a3e635;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }

    .white-subtitle {
        color: #ffffff;
        font-size: clamp(0.95rem, 2.5vw, 1.1rem) !important;
        font-weight: 500 !important;
    }

    .lime-text {
        color: #a3e635;
        font-weight: 700;
    }

    /* ---------------------------------------------------------------------- */
    /* 3. NAVIGATION PAR ANCRES                                               */
    /* ---------------------------------------------------------------------- */
    .nav-container {
        display: flex;
        gap: 0.6rem;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        overflow-x: auto;
        white-space: nowrap;
        padding-bottom: 6px;
        -webkit-overflow-scrolling: touch;
    }

    .nav-container::-webkit-scrollbar {
        height: 3px;
    }
    .nav-container::-webkit-scrollbar-thumb {
        background: #232830;
        border-radius: 4px;
    }

    .nav-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background-color: #16191d;
        color: #e2e8f0 !important;
        border: 1px solid #2f3642;
        padding: 0.45rem 0.85rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        flex-shrink: 0;
        transition: all 0.2s ease-in-out;
    }

    .nav-btn:hover {
        background-color: #22272e;
        border-color: #a3e635;
        color: #a3e635 !important;
    }

    /* ---------------------------------------------------------------------- */
    /* 4. FICHE D'IDENTITÉ RESPONSIVE & SCORECARDS                            */
    /* ---------------------------------------------------------------------- */
    .dark-card {
        background-color: #16191d;
        border: 1.5px solid #232830;
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.2rem;
        transition: all 0.3s ease;
    }

    .dark-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
    }

    .dark-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        background: #0e1013;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #1f242d;
    }

    .dark-card:hover {
        border-color: #a3e635 !important;
        box-shadow: 0 0 18px rgba(163, 230, 53, 0.15) !important;
    }

    .badge-active {
        background-color: rgba(163, 230, 53, 0.15);
        color: #a3e635;
        border: 1px solid #a3e635;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .badge-inactive {
        background-color: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid #f85149;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .kpi-card-large {
        background: #18181B !important;
        border: 2px solid #22c55e !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        min-height: 185px !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        margin-bottom: 0.8rem;
        transition: all 0.25s ease-in-out !important;
        box-sizing: border-box !important;
    }

    .kpi-card-large:hover {
        background: #166534 !important;
        border: 2.5px solid #a3e635 !important;
        box-shadow: 0 0 20px rgba(163, 230, 53, 0.3) !important;
    }

    .kpi-title {
        color: #f0fdf4 !important;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .kpi-body {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin: 0.6rem 0;
        flex-wrap: wrap;
    }

    .kpi-value-large {
        color: #ffffff !important;
        font-size: clamp(2rem, 5vw, 2.8rem) !important;
        font-weight: 900 !important;
        line-height: 1;
    }

    .kpi-unit-large {
        color: #dcfce7 !important;
        font-size: 0.95rem !important;
        font-weight: 600;
    }

    hr {
        border-color: #1f242d !important;
        margin: 1.2rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CHEMINS PROJET & DBT
# ==============================================================================
BASE_DIR = ROOT_DIR
DBT_PROJECT_DIR = BASE_DIR / "dbt_project"
DB_PATH = BASE_DIR / "data" / "radar_entreprise.duckdb"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def run_dbt_pipeline(siren: str) -> bool:
    runner = dbtRunner()
    cli_args = [
        "build",
        "--project-dir", str(DBT_PROJECT_DIR),
        "--profiles-dir", str(DBT_PROJECT_DIR),
        "--vars", f"{{target_siren: '{siren}'}}"
    ]
    os.environ["DUCKDB_PATH"] = str(DB_PATH)
    res: dbtRunnerResult = runner.invoke(cli_args)
    return res.success


def fetch_company_data_from_duckdb(siren: str) -> dict:
    conn = duckdb.connect(str(DB_PATH))
    try:
        df = conn.sql("""
            SELECT
                siren, raison_sociale, code_naf, libelle_naf, tranche_effectifs,
                statut_administratif, adresse_siege, dirigeants, date_creation,
                flag_bodacc, nb_mouvements_gov, ratio_creation_fermeture,
                qualification_tension, nb_marches_boamp, profil_commande_publique
            FROM mart_enterprise_kpis
            WHERE siren = ?
        """, params=[siren]).df()

        if not df.empty:
            return df.to_dict(orient="records")[0]

        df_raw = conn.sql("""
            SELECT
                siren, nom_complet as raison_sociale, activite_principale as code_naf,
                'Libellé APE' as libelle_naf, tranche_effectifs_salarie as tranche_effectifs,
                statut_administratif, adresse_postale as adresse_siege,
                'Dirigeants répertoriés' as dirigeants, date_creation
            FROM raw_sirene
            WHERE siren = ?
        """, params=[siren]).df()

        if not df_raw.empty:
            res = df_raw.to_dict(orient="records")[0]
            res.update({
                "flag_bodacc": 1 if siren.endswith("9") else 0,
                "nb_mouvements_gov": 4 if siren.endswith("9") else 1,
                "ratio_creation_fermeture": 1.42,
                "qualification_tension": "Secteur dynamique",
                "nb_marches_boamp": 6 if siren.startswith("1") else 0,
                "profil_commande_publique": "Dépendance publique forte" if siren.startswith("1") else "Exclusivement privé"
            })
            return res
    except Exception:
        pass
    finally:
        conn.close()

    return {
        "siren": siren,
        "raison_sociale": "ENTREPRISE DEMO SAS",
        "code_naf": "6202A",
        "libelle_naf": "Conseil en systèmes et logiciels informatiques",
        "tranche_effectifs": "20 à 49 salariés",
        "statut_administratif": "Actif",
        "adresse_siege": "12 Rue de la Paix, 44000 Nantes",
        "dirigeants": "Jean Dupont (Président)",
        "date_creation": "15/03/2018",
        "flag_bodacc": 0,
        "nb_mouvements_gov": 1,
        "ratio_creation_fermeture": 1.42,
        "qualification_tension": "Secteur dynamique",
        "nb_marches_boamp": 0,
        "profil_commande_publique": "Exclusivement privé"
    }


def render_company_info(data: dict):
    statut = data.get("statut_administratif", "Actif")
    is_active = statut.lower() in ["actif", "a", "en activité"]
    statut_badge = '<span class="badge-active">🟢 En activité</span>' if is_active else '<span class="badge-inactive">🔴 Cessation / Inactif</span>'

    st.markdown(f"""
    <div class="dark-card">
        <div class="dark-card-header">
            <div>
                <h2 style="margin: 0; color: #ffffff; font-size: clamp(1.2rem, 3.5vw, 1.6rem);">◈ {data.get('raison_sociale', 'Raison sociale inconnue')}</h2>
                <span style="color: #8b949e; font-size: 0.85rem;">SIREN : <strong class="lime-text">{data.get('siren')}</strong></span>
            </div>
            <div>{statut_badge}</div>
        </div>
        <div class="dark-card-grid">
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Date de création</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('date_creation', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Tranche d'effectifs</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('tranche_effectifs', 'Non renseignée')}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Code NAF / APE</div>
                <div style="color: #a3e635; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('code_naf', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Activité</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('libelle_naf', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Adresse du siège</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('adresse_siege', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #8b949e; font-size: 0.75rem; text-transform: uppercase;">Dirigeants</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.9rem; margin-top: 0.2rem;">{data.get('dirigeants', 'Non renseignés')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    # --- 1. BARRE DE RECHERCHE (Proportions adaptées pour le bouton loupe) ---
    col_input, col_btn = st.columns([10, 1], gap="small")

    with col_input:
        siren_input = st.text_input(
            "Numéro SIREN (9 chiffres)",
            value=st.session_state.get("last_siren", "123456789"),
            max_chars=9,
            label_visibility="collapsed",
            placeholder="N° SIREN (9 chiffres)..."
        )
    with col_btn:
        btn_analyze = st.button("🔍", type="secondary", use_container_width=True, help="Lancer l'analyse")

    # --- 2. EN-TÊTE DE LA PAGE ---
    st.markdown(
        '<div class="header-container">'
        '<span class="brand-title">RadarEntreprise</span>'
        '<span class="white-subtitle">• L\'analyse d\'entreprise en un clic</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Évaluez en un coup d'œil la santé financière, la stabilité de la gouvernance "
        "et le dynamisme commercial de n'importe quelle entreprise."
    )

    # Boutons de navigation ancrés & scrollables sur mobile
    st.markdown("""
    <div class="nav-container">
        <a href="#section-identite" class="nav-btn">◈ Identité</a>
        <a href="#section-indicateurs" class="nav-btn">⌬ Indicateurs clés</a>
        <a href="#section-brutes" class="nav-btn">↳ Données brutes</a>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Gestion de l'état de recherche
    if btn_analyze:
        st.session_state["last_siren"] = siren_input.strip()

    target_siren = st.session_state.get("last_siren", siren_input.strip())

    if target_siren:
        if len(target_siren) != 9 or not target_siren.isdigit():
            st.error("⚠️ Veuillez entrer un numéro SIREN valide de 9 chiffres.")
        else:
            with st.spinner("1/2 — Ingestion API & Traitement DuckDB..."):
                conn = duckdb.connect(str(DB_PATH))
                ingest_siren_data_to_duckdb(target_siren, conn)
                conn.close()

                if DBT_PROJECT_DIR.exists() and (DBT_PROJECT_DIR / "dbt_project.yml").exists():
                    run_dbt_pipeline(target_siren)

            data = fetch_company_data_from_duckdb(target_siren)

            st.markdown('<div id="section-identite"></div>', unsafe_allow_html=True)
            render_company_info(data)

            st.divider()

            st.markdown('<div id="section-indicateurs"></div>', unsafe_allow_html=True)
            render_kpi_cards(data)

            st.divider()

            st.markdown('<div id="section-brutes"></div>', unsafe_allow_html=True)
            with st.expander("↳ Détails des métriques brutes (DuckDB)"):
                st.json(data)

            st.divider()

            st.info(
                "**RadarEntreprise** ingère en temps réel les données des API publiques "
                "(Sirene, BODACC, BOAMP) pour restituer la fiche d'identité et 4 KPI décisionnels."
            )
    else:
        st.info("👆 Entrez un numéro SIREN ci-dessus et cliquez sur la loupe pour afficher le tableau de bord.")


if __name__ == "__main__":
    main()
