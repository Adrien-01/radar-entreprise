import os
import sys
import math
import subprocess
from pathlib import Path
import pandas as pd

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

# Import de la fonction d'ingestion interne
try:
    from src.ingestion.fetch_api import ingest_siren_data_to_duckdb
except ModuleNotFoundError:
    from ingestion.fetch_api import ingest_siren_data_to_duckdb

# ==============================================================================
# CONFIGURATION STREAMLIT & STYLES CSS RESPONSIVE & CARTES KPI
# ==============================================================================
st.set_page_config(
    page_title="RadarEntreprise",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

current_siren_val = st.session_state.get("last_siren", "")

st.markdown(f"""
<style>
    [data-testid="stHeader"] {{
        display: none !important;
    }}
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    #MainMenu {{
        visibility: hidden;
    }}
    footer {{
        visibility: hidden;
    }}
    html, body {{
        scroll-behavior: smooth;
        background-color: #0b0d0e !important;
    }}
    .stApp {{
        background-color: #0b0d0e;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .main .block-container {{
        padding-top: 5.2rem !important;
        padding-bottom: 2rem;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1200px;
    }}
    [data-testid="stHorizontalBlock"]:has(input[placeholder*="SIREN"]) {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        z-index: 999999 !important;
        background-color: rgba(11, 13, 14, 0.98) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 10px 2rem !important;
        box-sizing: border-box !important;
        border-bottom: 1px solid #1e2924 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6) !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
    }}
    [data-testid="stHorizontalBlock"]:has(input[placeholder*="SIREN"]) > [data-testid="column"] {{
        max-width: 1200px;
        margin: 0 auto;
    }}
    div[data-baseweb="input"] {{
        background-color: #0f1715 !important;
        border: 1.5px solid {'#a3e635' if len(current_siren_val) == 9 else '#1e2924'} !important;
        border-radius: 20px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a3e635' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'%3E%3C/line%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: 14px center !important;
        box-shadow: {'0 0 15px rgba(163, 230, 53, 0.3)' if len(current_siren_val) == 9 else 'none'} !important;
        transition: all 0.3s ease !important;
    }}
    div[data-baseweb="input"] input {{
        color: #ffffff !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        padding-left: 40px !important;
    }}
    div[data-baseweb="input"] input::placeholder {{
        color: #64748b !important;
    }}
    .stButton > button {{
        background-color: #0f1715 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 16px !important;
        border: 1.5px solid #1e2924 !important;
        padding: 0.5rem 1rem !important;
        height: 42px !important;
        transition: all 0.3s ease !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }}
    .stButton > button:hover {{
        background-color: #131d1a !important;
        border-color: #a3e635 !important;
        color: #a3e635 !important;
        box-shadow: 0 0 18px rgba(163, 230, 53, 0.25) !important;
    }}
    .header-container {{
        display: flex;
        align-items: baseline;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }}
    .brand-title {{
        font-size: clamp(2.2rem, 6vw, 3.8rem);
        font-weight: 800;
        color: #a3e635;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }}
    .white-subtitle {{
        color: #ffffff;
        font-size: clamp(0.95rem, 2.5vw, 1.1rem) !important;
        font-weight: 500 !important;
    }}
    .lime-text {{
        color: #a3e635;
        font-weight: 700;
    }}
    .nav-container {{
        display: flex;
        gap: 0.6rem;
    }}
    .nav-btn {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background-color: #0f1715;
        color: #e2e8f0 !important;
        border: 1px solid #1e2924;
        padding: 0.45rem 0.85rem;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        flex-shrink: 0;
        transition: all 0.2s ease-in-out;
    }}
    .nav-btn:hover {{
        background-color: #15201c;
        border-color: #a3e635;
        color: #a3e635 !important;
    }}

    /* ==============================================================================
       CARTE IDENTITÉ & FOND TEINTÉ VERT
       ============================================================================== */
    .dark-card {{
        background: linear-gradient(145deg, #12221a, #0a1410) !important;
        border: 1.5px solid rgba(163, 230, 53, 0.25) !important;
        border-radius: 18px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        transition: all 0.3s ease;
    }}
    .dark-card:hover {{
        border-color: #a3e635 !important;
        box-shadow: 0 8px 30px rgba(163, 230, 53, 0.15);
    }}
    .dark-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
    }}
    .dark-card-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        background: rgba(8, 14, 12, 0.7);
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(163, 230, 53, 0.15);
    }}
    .badge-active {{
        background-color: rgba(163, 230, 53, 0.2);
        color: #a3e635;
        border: 1px solid #a3e635;
        padding: 0.4rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        white-space: nowrap;
    }}
    .badge-inactive {{
        background-color: rgba(248, 81, 73, 0.2);
        color: #f85149;
        border: 1px solid #f85149;
        padding: 0.4rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        white-space: nowrap;
    }}

    /* ==============================================================================
       CARTES KPI 2x2 : ULTRA-VISUELLES + DEGRADÉ VERT NÉON + HOVER PUISSANT
       ============================================================================== */
    .kpi-card-large {{
        background: linear-gradient(145deg, #13271d 0%, #09130f 100%) !important;
        border: 1.5px solid rgba(163, 230, 53, 0.3) !important;
        border-radius: 18px !important;
        padding: 1.4rem !important;
        margin-bottom: 1rem;
        box-sizing: border-box;
        height: 230px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }}
    .kpi-card-large:hover {{
        border-color: #a3e635 !important;
        transform: translateY(-6px) scale(1.01) !important;
        background: linear-gradient(145deg, #1a3528 0%, #0d1a14 100%) !important;
        box-shadow: 0 14px 35px rgba(0, 0, 0, 0.7), 0 0 25px rgba(163, 230, 53, 0.3) !important;
    }}
    .kpi-card-body {{
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 0.6rem;
    }}
    .kpi-title {{
        color: #a3e635;
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 0.8px;
    }}
    .kpi-value-large {{
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        line-height: 1 !important;
        letter-spacing: -0.5px;
    }}
    .kpi-unit-large {{
        font-size: 1.1rem;
        color: #94a3b8;
        font-weight: 600;
        margin-left: 0.4rem;
    }}
    .kpi-footer {{
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        border-top: 1px solid rgba(163, 230, 53, 0.15);
        padding-top: 0.6rem;
        margin-top: auto;
    }}
    .badge-dark {{
        background-color: rgba(163, 230, 53, 0.12);
        color: #e2e8f0;
        border: 1px solid rgba(163, 230, 53, 0.3);
        padding: 0.35rem 0.85rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
    }}
    .badge-red {{
        background-color: rgba(248, 81, 73, 0.2);
        color: #ff6b6b;
        border: 1.5px solid #f85149;
        padding: 0.35rem 0.85rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# CHEMINS PROJET & DBT (Chemins relatifs / portables)
# ==============================================================================
BASE_DIR = ROOT_DIR
DBT_PROJECT_DIR = BASE_DIR / "radar_dbt_project"
DB_PATH = DBT_PROJECT_DIR / "data" / "radar_entreprise.duckdb"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def run_dbt_pipeline(siren: str) -> bool:
    try:
        dbt_executable = "dbt.exe" if os.name == "nt" else "dbt"
        venv_bin = Path(sys.prefix) / ("Scripts" if os.name == "nt" else "bin")
        potential_dbt = venv_bin / dbt_executable

        cmd_path = str(potential_dbt) if potential_dbt.exists() else "dbt"
        cmd = [cmd_path, "build", "--vars", f"{{target_siren: '{siren}'}}"]

        subprocess.run(
            cmd,
            cwd=str(DBT_PROJECT_DIR),
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or e.stdout or "Erreur inconnue"
        print(f"[DBT Subprocess Error]: {error_msg}")
        st.error(f"❌ Erreur technique dbt : {error_msg}")
        return False


def fetch_company_data_from_duckdb(siren: str) -> dict:
    with duckdb.connect(str(DB_PATH), read_only=True) as conn:
        table_exists = conn.sql(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mart_enterprise_kpis'"
        ).fetchone()[0] > 0

        if table_exists:
            df = conn.sql("""
                SELECT
                    siren, raison_sociale, code_naf, section_activite, tranche_effectifs,
                    statut_administratif, adresse_siege, dirigeants, date_creation,
                    flag_bodacc, nb_mouvements_gov, ratio_creation_fermeture,
                    annee_exercice, chiffre_affaires, resultat_net, marge_nette_pct,
                    sante_legale_label, gouvernance_label, phase_vie_label
                FROM mart_enterprise_kpis
                WHERE siren = ?
            """, params=[siren]).df()

            if not df.empty:
                return df.to_dict(orient="records")[0]

        df_raw = conn.sql("""
            SELECT
                siren, raison_sociale, code_naf, section_activite, tranche_effectifs,
                statut_administratif, adresse_siege, dirigeants, date_creation,
                nb_mouvements_gov
            FROM raw_sirene
            WHERE siren = ?
        """, params=[siren]).df()

        df_bodacc = conn.sql("""
            SELECT flag_bodacc FROM raw_bodacc WHERE siren = ?
        """, params=[siren]).df()

        df_finances = conn.sql("""
            SELECT annee, chiffre_affaires, resultat_net, marge_nette_pct
            FROM raw_finances
            WHERE siren = ?
            ORDER BY annee DESC
            LIMIT 1
        """, params=[siren]).df()

        if not df_raw.empty:
            res = df_raw.to_dict(orient="records")[0]
            flag_b = int(df_bodacc.iloc[0]["flag_bodacc"]) if not df_bodacc.empty else 0

            annee_ex = int(df_finances.iloc[0]["annee"]) if not df_finances.empty else None
            ca = df_finances.iloc[0]["chiffre_affaires"] if not df_finances.empty else None
            res_net = df_finances.iloc[0]["resultat_net"] if not df_finances.empty else None
            marge = df_finances.iloc[0]["marge_nette_pct"] if not df_finances.empty else None

            res.update({
                "flag_bodacc": flag_b,
                "nb_mouvements_gov": res.get("nb_mouvements_gov", 1),
                "ratio_creation_fermeture": 1.42,
                "annee_exercice": annee_ex,
                "chiffre_affaires": ca,
                "resultat_net": res_net,
                "marge_nette_pct": marge,
                "sante_legale_label": "EN VIGILANCE" if flag_b == 1 else "SAIN",
                "gouvernance_label": "SIGNAL D'INSTABILITÉ" if res.get("nb_mouvements_gov", 0) >= 3 else "STABLE",
                "phase_vie_label": "Entreprise Établie"
            })
            return res

    raise ValueError(f"Aucune donnée trouvée en base pour le SIREN : {siren}")


def render_kpi_cards(kpi_data: dict):
    """
    Rend une grille de 4 KPI décisionnels au format 2x2 harmonisé avec visuel fort.
    Gère proprement l'absence de données financières (NaN / None) sans afficher de code HTML brut.
    """
    # Ligne 1 : Santé légale et Gouvernance
    col1, col2 = st.columns(2)

    # 1. SCORE DE SANTÉ LÉGALE (BODACC - 24 mois)
    with col1:
        flag_bodacc = kpi_data.get("flag_bodacc", 0)
        is_procedure = (flag_bodacc == 1)
        status_label = "1 • PROCÉDURE ACTIVE" if is_procedure else "0 • SAIN"
        badge_class = "badge-red" if is_procedure else "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div class="kpi-title">Santé Légale (24m)</div>
                    <div style="margin-top: 12px;">
                        <span class="{badge_class}" style="font-size: 1.1rem; padding: 8px 18px;">{status_label}</span>
                    </div>
                </div>
                <div class="kpi-footer">Source : BODACC</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. INDICE D'INSTABILITÉ DE LA GOUVERNANCE (24 mois)
    with col2:
        mouvements = kpi_data.get("nb_mouvements_gov", 0)
        is_unstable = (mouvements >= 3)
        badge_label = "SIGNAL D'INSTABILITÉ" if is_unstable else "STABLE"
        badge_class = "badge-red" if is_unstable else "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div class="kpi-title">Gouvernance (24m)</div>
                    <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                        <span class="kpi-value-large">{mouvements}</span>
                        <span class="kpi-unit-large">mouvements</span>
                    </div>
                    <div>
                        <span class="{badge_class}">{badge_label}</span>
                    </div>
                </div>
                <div class="kpi-footer">Seuil : ≥ 3 mouvements</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Ligne 2 : Tension sectorielle et Performance Financière
    col3, col4 = st.columns(2)

    # 3. TENSION SECTORIELLE RÉGIONALE (INSEE - 12 mois)
    with col3:
        ratio = kpi_data.get("ratio_creation_fermeture", 1.0)
        qualification = kpi_data.get("qualification_tension", "Secteur stable")

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div class="kpi-title">Tension Sectorielle</div>
                    <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                        <span class="kpi-value-large">{ratio:.2f}</span>
                        <span class="kpi-unit-large">créations / fermeture</span>
                    </div>
                    <div>
                        <span class="badge-dark">{qualification}</span>
                    </div>
                </div>
                <div class="kpi-footer">Ratio NAF / Dép (12m)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. PERFORMANCE FINANCIÈRE (Dernier exercice)
    with col4:
        ca = kpi_data.get("chiffre_affaires")
        resultat = kpi_data.get("resultat_net")
        marge = kpi_data.get("marge_nette_pct")
        annee = kpi_data.get("annee_exercice")

        # Fonction utilitaire de contrôle de valeur nulle/NaN
        def is_valid_num(val):
            if val is None or pd.isna(val):
                return False
            try:
                return not math.isnan(float(val))
            except (ValueError, TypeError):
                return False

        has_financial_data = is_valid_num(ca) or is_valid_num(resultat) or is_valid_num(marge)

        if has_financial_data:
            annee_title = f" ({int(annee)})" if is_valid_num(annee) else ""
            ca_formatted = f"{float(ca):,.0f} €".replace(",", " ") if is_valid_num(ca) else "N/A"
            res_formatted = f"{float(resultat):,.0f} €".replace(",", " ") if is_valid_num(resultat) else "N/A"
            marge_formatted = f"{float(marge):.1f}%" if is_valid_num(marge) else "N/A"

            rentabilite_label = kpi_data.get("rentabilite_label")
            if not rentabilite_label:
                marge_val = float(marge) if is_valid_num(marge) else None
                if marge_val is None:
                    rentabilite_label = "NON RENSEIGNÉ"
                elif marge_val < 1.0:
                    rentabilite_label = "MARGE FAIBLE"
                elif marge_val <= 3.5:
                    rentabilite_label = "MARGE CONFORME"
                else:
                    rentabilite_label = "FORTE RENTABILITÉ"

            marge_badge_class = "badge-red" if (is_valid_num(marge) and float(marge) < 1.0) else "badge-dark"

            card_html = f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div class="kpi-title">Performance Financière{annee_title}</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span class="kpi-value-large">{marge_formatted}</span>
                            <span class="kpi-unit-large">Marge Nette</span>
                        </div>
                        <span class="{marge_badge_class}">{rentabilite_label}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.4; margin-top: 4px;">
                        <div><b>CA :</b> {ca_formatted}</div>
                        <div><b>Résultat Net :</b> {res_formatted}</div>
                    </div>
                </div>
                <div class="kpi-footer">Source : API Recherche Entreprises</div>
            </div>
            """
        else:
            card_html = """
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div class="kpi-title">Performance Financière</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span class="kpi-value-large" style="color: #94a3b8 !important;">N/A</span>
                            <span class="kpi-unit-large" style="font-size: 0.95rem;">Comptes non disponibles</span>
                        </div>
                        <span class="badge-dark" style="opacity: 0.7;">NON RENSEIGNÉ</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; font-style: italic; margin-top: 6px;">
                        Bilans financiers confidentiels ou non déposés auprès du greffe du tribunal de commerce.
                    </div>
                </div>
                <div class="kpi-footer">Source : API Recherche Entreprises</div>
            </div>
            """

        st.markdown(card_html, unsafe_allow_html=True)


def render_company_info(data: dict):
    statut = data.get("statut_administratif", "Actif")
    is_active = str(statut).lower() in ["actif", "a", "en activité"]
    statut_badge = '<span class="badge-active">🟢 En activité</span>' if is_active else '<span class="badge-inactive">🔴 Cessation / Inactif</span>'

    st.markdown(f"""
    <div class="dark-card">
        <div class="dark-card-header">
            <div>
                <h2 style="margin: 0; color: #ffffff; font-size: clamp(1.3rem, 3.5vw, 1.8rem); font-weight: 800;">◈ {data.get('raison_sociale', 'Raison sociale inconnue')}</h2>
                <span style="color: #94a3b8; font-size: 0.9rem;">SIREN : <strong class="lime-text">{data.get('siren')}</strong></span>
            </div>
            <div>{statut_badge}</div>
        </div>
        <div class="dark-card-grid">
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Date de création</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('date_creation', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Tranche d'effectifs</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('tranche_effectifs', 'Non renseignée')}</div>
            </div>
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Code NAF / APE</div>
                <div style="color: #ffffff; font-weight: 700; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('code_naf', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Activité</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('section_activite', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Adresse du siège</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('adresse_siege', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #a3e635; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">Dirigeants</div>
                <div style="color: #ffffff; font-weight: 600; font-size: 0.95rem; margin-top: 0.2rem;">{data.get('dirigeants', 'Non renseignés')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    col_input, col_btn = st.columns([10, 1], gap="small")

    with col_input:
        siren_input = st.text_input(
            "Numéro SIREN (9 chiffres)",
            value=st.session_state.get("last_siren", ""),
            max_chars=9,
            label_visibility="collapsed",
            placeholder="N° SIREN (9 chiffres)...",
            on_change=lambda: st.rerun()
        )
    with col_btn:
        btn_analyze = st.button("Recherche", type="secondary", use_container_width=True, help="Lancer l'analyse")

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

    if btn_analyze:
        st.session_state["last_siren"] = siren_input.strip()

    target_siren = st.session_state.get("last_siren", siren_input.strip())

    if target_siren:
        col_nav, col_back = st.columns([10, 1], gap="small")
        with col_nav:
            st.markdown("""
            <div class="nav-container">
                <a href="#section-identite" class="nav-btn">◈ Identité</a>
                <a href="#section-indicateurs" class="nav-btn">⌬ Indicateurs clés</a>
                <a href="#section-brutes" class="nav-btn">↳ Données brutes</a>
            </div>
            """, unsafe_allow_html=True)
        with col_back:
            if st.button("↩", type="secondary", use_container_width=True, help="Retour à l'accueil"):
                st.session_state["last_siren"] = ""
                st.rerun()
    else:
        st.markdown("""
        <div class="nav-container">
            <a href="#section-identite" class="nav-btn">◈ Identité</a>
            <a href="#section-indicateurs" class="nav-btn">⌬ Indicateurs clés</a>
            <a href="#section-brutes" class="nav-btn">↳ Données brutes</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if target_siren:
        if len(target_siren) != 9 or not target_siren.isdigit():
            st.error("⚠️ Veuillez entrer un numéro SIREN valide comportant exactement 9 chiffres.")
        else:
            try:
                with st.spinner("1/2 — Ingestion API officielle & Traitement DuckDB..."):
                    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

                    conn = duckdb.connect(str(DB_PATH), read_only=False)
                    try:
                        ingest_siren_data_to_duckdb(target_siren, conn)
                    finally:
                        conn.close()

                    if DBT_PROJECT_DIR.exists() and (DBT_PROJECT_DIR / "dbt_project.yml").exists():
                        success = run_dbt_pipeline(target_siren)
                        if not success:
                            st.warning("⚠️ Le pipeline dbt s'est exécuté avec des avertissements ou erreurs.")

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
                    "(Sirene, BODACC, Financement, INSEE) pour restituer la fiche d'identité et les indicateurs clés."
                )

            except Exception as e:
                st.error(f"❌ **Erreur de recherche :** Impossible de trouver ou de récupérer les données pour le SIREN `{target_siren}`. ({e})")
    else:
        st.info("👆 Entrez un numéro SIREN ci-dessus et cliquez sur la loupe pour afficher le tableau de bord.")


if __name__ == "__main__":
    main()
