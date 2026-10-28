import gc
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

# resolution des imports
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent if CURRENT_DIR.name == "src" else CURRENT_DIR

for path in [str(ROOT_DIR), str(CURRENT_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

import duckdb
import streamlit as st

try:
    from src.ingestion.fetch_api import ingest_siren_data_to_duckdb
except ModuleNotFoundError:
    from ingestion.fetch_api import ingest_siren_data_to_duckdb

# configuration de l'application et styles
st.set_page_config(
    page_title="RadarEntreprise",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "last_siren" not in st.session_state:
    st.session_state["last_siren"] = ""

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
        box-shadow: {'0 0 15px rgba(163, 230, 53, 0.3)' if len(current_siren_val) == 9 else 'none'} !important;
        transition: all 0.3s ease !important;
    }}
    div[data-baseweb="input"] input {{
        color: #ffffff !important;
        background-color: transparent !important;
        font-weight: 600 !important;
        padding-left: 16px !important;
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
    .dark-card {{
        background: linear-gradient(145deg, #12221a, #0a1410) !important;
        border: 1.5px solid rgba(163, 230, 53, 0.25) !important;
        border-radius: 18px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        transition: all 0.4s ease;
    }}
    .dark-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1.2rem;
        flex-wrap: wrap;
    }}
    .dark-card:hover {{
        transform: translateY(-3px);
        border-color: #a3e635 !important;
        box-shadow: 0 10px 30px rgba(163, 230, 53, 0.2);;
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
        transition: all 0.4s ease;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }}
    .kpi-card-large:hover {{
        transform: translateY(-4px);
        border-color: #a3e635 !important;
        box-shadow: 0 12px 30px rgba(163, 230, 53, 0.25);
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
    .badge-orange {{
        background-color: rgba(245, 158, 11, 0.18);
        color: #f59e0b;
        border: 1.5px solid #f59e0b;
        padding: 0.35rem 0.85rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
    }}
    .kpi-card-custom {{
        background: linear-gradient(145deg, #162620 0%, #0d1713 100%) !important;
        border: 1.5px solid rgba(163, 230, 53, 0.3) !important;
        border-radius: 18px !important;
        padding: 1.4rem !important;
        height: 340px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5) !important;
        transition: all 0.4s ease !important;
    }}
    .kpi-card-custom:hover {{
        transform: translateY(-4px) !important;
        border-color: #a3e635 !important;
        box-shadow: 0 12px 30px rgba(163, 230, 53, 0.2) !important;
    }}
</style>
""", unsafe_allow_html=True)

# gestion des chemins et pipeline dbt
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
        cmd = [
            cmd_path,
            "build",
            "--profiles-dir", ".",
            "--vars", f"{{target_siren: '{siren}'}}"
        ]

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
        st.error(f"Erreur technique dbt : {error_msg}")
        return False


def fetch_company_data_from_duckdb(siren: str) -> dict:
    with duckdb.connect(str(DB_PATH), read_only=True) as conn:
        count_result = conn.sql(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'mart_enterprise_kpis'"
        ).limit(1).fetchall()

        table_exists = count_result[0][0] > 0 if count_result else False

        if table_exists:
            df = conn.sql("""
                SELECT
                    k.siren, k.raison_sociale, k.code_naf, k.section_activite, k.tranche_effectifs,
                    k.statut_administratif, k.adresse_siege, k.dirigeants, k.date_creation,
                    COALESCE(b.flag_bodacc, 0) AS flag_bodacc,
                    COALESCE(b.procedure_label, 'Aucune procédure détectée') AS procedure_label,
                    k.mouvements_24m, k.nb_mouvements_gov,
                    k.nb_creations_12m, k.nb_fermetures_12m, k.ratio_creation_fermeture,
                    k.annee_exercice, k.chiffre_affaires, k.resultat_net, k.marge_nette_pct,
                    k.sante_legale_label, k.gouvernance_label, k.phase_vie_label
                FROM mart_enterprise_kpis k
                LEFT JOIN raw_bodacc b ON k.siren = b.siren
                WHERE k.siren = ?
            """, params=[siren]).df()

            if not df.empty:
                record = df.to_dict(orient="records")[0]
                if "mouvements_24m" not in record or record["mouvements_24m"] is None:
                    record["mouvements_24m"] = record.get("nb_mouvements_gov", 0)
                return record

        df_raw = conn.sql("""
            SELECT
                siren, raison_sociale, code_naf, section_activite, tranche_effectifs,
                statut_administratif, adresse_siege, dirigeants, date_creation,
                departement, nb_mouvements_gov
            FROM raw_sirene
            WHERE siren = ?
        """, params=[siren]).df()

        df_bodacc = conn.sql("""
            SELECT flag_bodacc, procedure_label FROM raw_bodacc WHERE siren = ?
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
            code_naf = res.get("code_naf")
            dept = res.get("departement")

            df_demog = conn.sql("""
                SELECT nb_creations_12m, nb_fermetures_12m, ratio_creation_fermeture
                FROM raw_insee_demographie
                WHERE code_naf = ? AND departement = ?
            """, params=[code_naf, dept]).df()

            nb_crea = int(df_demog.iloc[0]["nb_creations_12m"]) if not df_demog.empty else 0
            nb_ferm = int(df_demog.iloc[0]["nb_fermetures_12m"]) if not df_demog.empty else 0

            if not df_demog.empty and df_demog.iloc[0]["ratio_creation_fermeture"] is not None:
                ratio_calc = float(df_demog.iloc[0]["ratio_creation_fermeture"])
            else:
                ratio_calc = round(nb_crea / max(nb_ferm, 1), 2) if (nb_crea or nb_ferm) else 1.0

            flag_b = int(df_bodacc.iloc[0]["flag_bodacc"]) if not df_bodacc.empty else 0
            proc_label = df_bodacc.iloc[0].get("procedure_label", "Aucune procédure détectée") if not df_bodacc.empty else "Aucune procédure détectée"
            nb_mouv = res.get("nb_mouvements_gov", 0)

            annee_ex = int(df_finances.iloc[0]["annee"]) if not df_finances.empty else None
            ca = df_finances.iloc[0]["chiffre_affaires"] if not df_finances.empty else None
            res_net = df_finances.iloc[0]["resultat_net"] if not df_finances.empty else None
            marge = df_finances.iloc[0]["marge_nette_pct"] if not df_finances.empty else None

            res.update({
                "flag_bodacc": flag_b,
                "procedure_label": proc_label,
                "nb_mouvements_gov": nb_mouv,
                "mouvements_24m": nb_mouv,
                "nb_creations_12m": nb_crea,
                "nb_fermetures_12m": nb_ferm,
                "ratio_creation_fermeture": ratio_calc,
                "annee_exercice": annee_ex,
                "chiffre_affaires": ca,
                "resultat_net": res_net,
                "marge_nette_pct": marge,
                "sante_legale_label": "EN VIGILANCE" if flag_b == 1 else "SAIN",
                "gouvernance_label": "STABLE",
                "phase_vie_label": "Entreprise Etablie"
            })
            return res

    raise ValueError(f"Aucune donnee trouvee en base pour le SIREN : {siren}")

# rendu des composants visuels
def render_kpi_cards(kpi_data: dict):
    col1, col2 = st.columns(2)

    with col1:
        flag_bodacc = kpi_data.get("flag_bodacc", 0)
        mouvements_24m = kpi_data.get("mouvements_24m", kpi_data.get("nb_mouvements_gov", 0))
        procedure_label = kpi_data.get("procedure_label", "Procedure active")
        is_procedure = (flag_bodacc == 1)

        mouv_label = "mouvement" if mouvements_24m <= 1 else "mouvements"

        if is_procedure:
            status_label = f"1 - {procedure_label.upper()}"
            badge_class = "badge-red"
        elif mouvements_24m >= 5:
            status_label = "VIGILANCE"
            badge_class = "badge-orange"
        elif mouvements_24m > 0:
            status_label = "SAIN"
            badge_class = "badge-dark"
        else:
            status_label = "0 - SAIN"
            badge_class = "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="kpi-title">Sante Legale (24m)</div>
                        <span class="{badge_class}">{status_label}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="kpi-value-large">{mouvements_24m}</span>
                        <span class="kpi-unit-large">{mouv_label}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem; color: #94a3b8;">
                        Evolution legale et modifications (24m)
                    </div>
                </div>
                <div class="kpi-footer">Source : BODACC</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        nb_dirigeants = kpi_data.get("nb_mouvements_gov", 0)
        dirigeant_label = "dirigeant" if nb_dirigeants <= 1 else "dirigeants"

        if nb_dirigeants <= 1:
            struct_label = "Unipersonnelle"
        elif nb_dirigeants <= 3:
            struct_label = "Gouvernance resserree"
        else:
            struct_label = "Gouvernance collegiale"

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="kpi-title">Taille de la Gouvernance</div>
                        <span class="badge-dark">{struct_label}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="kpi-value-large">{nb_dirigeants}</span>
                        <span class="kpi-unit-large">{dirigeant_label}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem; color: #94a3b8;">
                        Mandataires actuels en poste
                    </div>
                </div>
                <div class="kpi-footer">Source : API Sirene</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    col3, col4 = st.columns(2)

    with col3:
        ratio = kpi_data.get("ratio_creation_fermeture", 1.0)
        qualification = kpi_data.get("qualification_tension", "Secteur stable")

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="kpi-title">Tension Sectorielle</div>
                        <span class="badge-dark">{qualification}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="kpi-value-large">{ratio:.2f}</span>
                        <span class="kpi-unit-large">creations / fermeture</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 0.85rem; color: #94a3b8;">
                        Ratio NAF / Dep (12m)
                    </div>
                </div>
                <div class="kpi-footer">Source : INSEE</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        ca = kpi_data.get("chiffre_affaires")
        resultat = kpi_data.get("resultat_net")
        marge = kpi_data.get("marge_nette_pct")
        annee = kpi_data.get("annee_exercice")

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
            ca_formatted = f"{float(ca):,.0f} EUR".replace(",", " ") if is_valid_num(ca) else "N/A"
            res_formatted = f"{float(resultat):,.0f} EUR".replace(",", " ") if is_valid_num(resultat) else "N/A"
            marge_formatted = f"{float(marge):.1f}%" if is_valid_num(marge) else "N/A"

            rentabilite_label = kpi_data.get("rentabilite_label")
            if not rentabilite_label:
                marge_val = float(marge) if is_valid_num(marge) else None
                if marge_val is None:
                    rentabilite_label = "NON RENSEIGNE"
                elif marge_val < 1.0:
                    rentabilite_label = "MARGE FAIBLE"
                elif marge_val <= 3.5:
                    rentabilite_label = "MARGE CONFORME"
                else:
                    rentabilite_label = "FORTE RENTABILITE"

            marge_badge_class = "badge-red" if (is_valid_num(marge) and float(marge) < 1.0) else "badge-dark"

            card_html = f"""
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="kpi-title">Performance Financiere{annee_title}</div>
                        <span class="{marge_badge_class}">{rentabilite_label}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="kpi-value-large">{marge_formatted}</span>
                        <span class="kpi-unit-large">Marge Nette</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 6px;">
                        <div><b>CA :</b> {ca_formatted}</div>
                        <div><b>Resultat Net :</b> {res_formatted}</div>
                    </div>
                </div>
                <div class="kpi-footer">Source : API Recherche Entreprises</div>
            </div>
            """
        else:
            card_html = """
            <div class="kpi-card-large">
                <div class="kpi-card-body">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div class="kpi-title">Performance Financiere</div>
                        <span class="badge-dark" style="opacity: 0.7;">NON RENSEIGNE</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <span class="kpi-value-large" style="color: #94a3b8 !important; font-size: 2rem !important;">N/A</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94a3b8; font-style: italic; margin-top: 4px;">
                        Bilans financiers non deposes ou confidentiels.
                    </div>
                </div>
                <div class="kpi-footer">Source : API Recherche Entreprises</div>
            </div>
            """

        st.markdown(card_html, unsafe_allow_html=True)


def render_predictive_score_card(kpi_data: dict):
    flag_bodacc = int(kpi_data.get("flag_bodacc") or 0)
    procedure_label = kpi_data.get("procedure_label", "")

    # Si l'entreprise est en liquidation judiciaire, le score est directement à 0
    is_liquidation = flag_bodacc == 1 and ("liquidation" in procedure_label.lower())

    if is_liquidation:
        score = 0
        details_score = [("<span style='color: #f87171;'>●</span>", f"Procédure en cours : {procedure_label} (Score fixé à 0)")]
    else:
        score = 100
        details_score = []

        if flag_bodacc == 1:
            score -= 50
            details_score.append(("<span style='color: #f87171;'>●</span>", f"Procédure collective en cours : {procedure_label} (-50 pts)"))
        else:
            details_score.append(("<span style='color: #a3e635;'>●</span>", "Aucune procédure BODACC (+0 pt)"))

        marge = kpi_data.get("marge_nette_pct")
        if marge is not None and not pd.isna(marge):
            marge_val = float(marge)
            if marge_val > 3.0:
                score += 15
                details_score.append(("<span style='color: #a3e635;'>●</span>", f"Marge nette solide ({marge_val:.1f}%) (+15 pts)"))
            elif marge_val >= 1.0:
                score += 5
                details_score.append(("<span style='color: #fbbf24;'>●</span>", f"Marge nette correcte ({marge_val:.1f}%) (+5 pts)"))
            else:
                score -= 15
                details_score.append(("<span style='color: #f87171;'>●</span>", f"Marge nette faible ({marge_val:.1f}%) (-15 pts)"))
        else:
            score -= 10
            details_score.append(("<span style='color: #94a3b8;'>●</span>", "Données financières non communiquées (-10 pts)"))

        mouvements = int(kpi_data.get("mouvements_24m") or 0)
        if mouvements >= 5:
            score -= 20
            details_score.append(("<span style='color: #fbbf24;'>●</span>", f"Forte instabilité ({mouvements} mouvements) (-20 pts)"))
        elif mouvements > 0:
            score -= 5
            details_score.append(("<span style='color: #fbbf24;'>●</span>", f"Mouvements détectés ({mouvements}) (-5 pts)"))
        else:
            score += 10
            details_score.append(("<span style='color: #a3e635;'>●</span>", "Stabilité des mandats (0 mouvement) (+10 pts)"))

        score = max(0, min(100, score))

    if score >= 75:
        badge_score_class = "badge-dark"
        libelle_score = "ENTREPRISE SOLIDE"
        couleur_jauge = "#a3e635"
    elif score >= 40:
        badge_score_class = "badge-orange"
        libelle_score = "VIGILANCE MODÉRÉE"
        couleur_jauge = "#fbbf24"
    else:
        badge_score_class = "badge-red"
        libelle_score = "LIQUIDATION / RISQUE" if is_liquidation else "RISQUE ÉLEVÉ"
        couleur_jauge = "#f87171"

    factors_items = "".join([f"<div style='margin-bottom: 2px;'>{dot} {text}</div>" for dot, text in details_score])

    html_content = f"""
    <div class="kpi-card-custom">
        <div style="height: 190px;">
            <div style="display: flex; justify-content: space-between; align-items: center; min-height: 32px;">
                <span style="font-size: 0.82rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">
                    Indice de Solidité Global
                </span>
                <span class="{badge_score_class}">{libelle_score}</span>
            </div>
            <div style="margin-top: 10px; text-align: center;">
                <span style="font-size: 3.6rem; font-weight: 800; color: {couleur_jauge}; line-height: 1;">{score}</span>
                <span style="font-size: 1.4rem; color: #64748b; font-weight: 600;">/100</span>
            </div>
        </div>
        <div style="height: 90px; display: flex; flex-direction: column; justify-content: flex-end;">
            <hr style="border: none; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 0 0 8px 0;">
            <div style="font-size: 0.73rem; color: #cbd5e1; background: rgba(15, 23, 42, 0.6); padding: 8px 10px; border-radius: 6px; line-height: 1.2;">
                <div style="font-weight: 700; color: #f1f5f9; margin-bottom: 3px;">Facteurs clés du modèle :</div>
                {factors_items}
            </div>
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def render_company_info(data: dict):
    flag_bodacc = int(data.get("flag_bodacc") or 0)
    procedure_label = data.get("procedure_label", "")
    statut = data.get("statut_administratif", "Actif")

    # Correction de la cohérence : si un flag BODACC est actif (ex: liquidation), on l'affiche prioritairement
    if flag_bodacc == 1:
        statut_badge = f'<span class="badge-inactive">{procedure_label.upper()}</span>'
    else:
        is_active = str(statut).lower() in ["actif", "a", "en activite"]
        statut_badge = '<span class="badge-active">En activité</span>' if is_active else '<span class="badge-inactive">Cessation / Inactif</span>'

    st.markdown(f"""
    <div class="dark-card">
        <div class="dark-card-header">
            <div>
                <h2 style="margin: 0; color: #ffffff; font-size: clamp(1.3rem, 3.5vw, 1.8rem); font-weight: 800;">{data.get('raison_sociale', 'Raison sociale inconnue')}</h2>
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

# programme principal streamlit
def main():
    col_input, col_btn = st.columns([10, 1], gap="small")

    def update_siren_from_input():
        val = st.session_state.get("input_siren_widget", "").strip()
        if val:
            st.session_state["last_siren"] = val

    with col_input:
        siren_input = st.text_input(
            "Numero SIREN (9 chiffres)",
            value=st.session_state.get("last_siren", ""),
            key="input_siren_widget",
            max_chars=9,
            label_visibility="collapsed",
            placeholder="Numero SIREN (9 chiffres)...",
            on_change=update_siren_from_input
        )

    with col_btn:
        btn_analyze = st.button("Recherche", type="secondary", use_container_width=True, help="Lancer l'analyse")

    st.markdown(
        '<div class="header-container">'
        '<span class="brand-title">RadarEntreprise</span>'
        '<span class="white-subtitle">- L\'analyse d\'entreprise en un clic</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Evaluez en un coup d'oeil la sante financiere, la stabilite de la gouvernance "
        "et le dynamisme commercial de n'importe quelle entreprise."
    )

    if btn_analyze:
        st.session_state["last_siren"] = siren_input.strip()

    target_siren = st.session_state.get("last_siren", "").strip()

    if target_siren:
        col_nav, col_back = st.columns([10, 1], gap="small")
        with col_nav:
            st.markdown("""
            <div class="nav-container">
                <a href="#section-identite" class="nav-btn">Identite</a>
                <a href="#section-indicateurs" class="nav-btn">Indicateurs cles</a>
                <a href="#section-brutes" class="nav-btn">Donnees brutes</a>
            </div>
            """, unsafe_allow_html=True)
        with col_back:
            if st.button("Retour", type="secondary", use_container_width=True, help="Retour a l'accueil"):
                st.session_state["last_siren"] = ""
                st.session_state["input_siren_widget"] = ""
                st.rerun()
    else:
        st.markdown("""
        <div class="nav-container">
            <a href="#section-identite" class="nav-btn">Identite</a>
            <a href="#section-indicateurs" class="nav-btn">Indicateurs cles</a>
            <a href="#section-brutes" class="nav-btn">Donnees brutes</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if target_siren:
        if len(target_siren) != 9 or not target_siren.isdigit():
            st.error("Veuillez entrer un numero SIREN valide comportant exactement 9 chiffres.")
        else:
            try:
                with st.spinner("Ingestion API officielle et traitement dbt en cours..."):
                    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

                    conn = duckdb.connect(str(DB_PATH), read_only=False)
                    try:
                        ingest_siren_data_to_duckdb(target_siren, conn)
                    finally:
                        conn.close()

                    gc.collect()
                    time.sleep(0.3)

                    if DBT_PROJECT_DIR.exists() and (DBT_PROJECT_DIR / "dbt_project.yml").exists():
                        success = run_dbt_pipeline(target_siren)
                        if not success:
                            st.warning("Le pipeline dbt s'est execute avec des avertissements ou erreurs.")

                data = fetch_company_data_from_duckdb(target_siren)

                st.markdown('<div id="section-identite"></div>', unsafe_allow_html=True)
                render_company_info(data)

                st.divider()

                st.markdown('<div id="section-indicateurs"></div>', unsafe_allow_html=True)
                render_kpi_cards(data)

                st.divider()

                st.markdown("<br>", unsafe_allow_html=True)
                col_gauche, col_droite = st.columns(2)

                with col_gauche:
                    render_predictive_score_card(data)

                with col_droite:
                    creations = int(data.get("nb_creations_12m") or 0)
                    fermetures = int(data.get("nb_fermetures_12m") or 0)

                    total_flux = creations + fermetures
                    if total_flux > 0:
                        deg_creations = (creations / total_flux) * 360
                        pct_creations = (creations / total_flux) * 100
                        pct_fermetures = (fermetures / total_flux) * 100
                    else:
                        deg_creations = 180
                        pct_creations = 50.0
                        pct_fermetures = 50.0

                    html_chart_card = f"""
                    <div class="kpi-card-custom">
                        <div style="height: 190px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; min-height: 32px;">
                                <span style="font-size: 0.82rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; text-transform: uppercase;">
                                    Répartition des Flux (12m)
                                </span>
                                <span class="badge-dark" style="visibility: hidden;">SYNCHRO</span>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-around; height: 130px; padding: 5px 0 0 0;">
                                <!-- Camembert / Donut en CSS Conic Gradient -->
                                <div style="
                                    width: 100px;
                                    height: 100px;
                                    border-radius: 50%;
                                    background: conic-gradient(#a3e635 0deg {deg_creations}deg, #f87171 {deg_creations}deg 360deg);
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                                    position: relative;
                                ">
                                    <!-- Trou central pour effet Donut (optionnel, supprimez la div interne si vous voulez un camembert plein) -->
                                    <div style="
                                        width: 60px;
                                        height: 60px;
                                        border-radius: 50%;
                                        background: #0d1713;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        font-size: 0.7rem;
                                        font-weight: 700;
                                        color: #94a3b8;
                                    ">
                                        {total_flux}
                                    </div>
                                </div>
                                <!-- Légende explicative -->
                                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span style="width: 12px; height: 12px; background: #a3e635; border-radius: 3px;"></span>
                                        <span style="color: #ffffff; font-weight: 600;">Créations :</span>
                                        <span style="color: #a3e635; font-weight: 700;">{creations} ({pct_creations:.1f}%)</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span style="width: 12px; height: 12px; background: #f87171; border-radius: 3px;"></span>
                                        <span style="color: #ffffff; font-weight: 600;">Fermetures :</span>
                                        <span style="color: #f87171; font-weight: 700;">{fermetures} ({pct_fermetures:.1f}%)</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style="height: 90px; display: flex; flex-direction: column; justify-content: flex-end;">
                            <hr style="border: none; border-top: 1px solid rgba(255, 255, 255, 0.1); margin: 0 0 8px 0;">
                            <div style="font-size: 0.73rem; color: #cbd5e1; background: rgba(15, 23, 42, 0.6); padding: 8px 10px; border-radius: 6px; text-align: center;">
                                Proportion des flux sur les 12 derniers mois (INSEE)
                            </div>
                        </div>
                    </div>
                    """

                    st.markdown(html_chart_card, unsafe_allow_html=True)

                st.divider()

                st.markdown('<div id="section-brutes"></div>', unsafe_allow_html=True)
                with st.expander("Details des metriques brutes (DuckDB)"):
                    st.json(data)

                st.divider()

                st.info(
                    "RadarEntreprise ingere en temps reel les donnees des API publiques "
                    "(Sirene, BODACC, Financement, INSEE) pour restituer la fiche d'identite et les indicateurs cles."
                )

            except Exception as e:  # noqa: BLE001
                st.error(f"Erreur de recherche : Impossible de trouver ou de recuperer les donnees pour le SIREN `{target_siren}`...")
    else:
        st.info("Entrez un numero SIREN ci-dessus et cliquez sur la loupe pour afficher le tableau de bord.")


if __name__ == "__main__":
    main()
