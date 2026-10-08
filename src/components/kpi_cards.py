import streamlit as st

def render_kpi_cards(kpi_data: dict):
    """
    Rend une grille de 4 KPI décisionnels au format 2x2.
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
                <div class="kpi-title">Santé Légale (24m)</div>
                <div class="kpi-body">
                    <span class="{badge_class}">{status_label}</span>
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
                <div class="kpi-title">Gouvernance (24m)</div>
                <div class="kpi-body">
                    <span class="kpi-value-large">{mouvements}</span>
                    <span class="kpi-unit-large">mouvt.</span>
                    <span class="{badge_class}">{badge_label}</span>
                </div>
                <div class="kpi-footer">Seuil : ≥ 3 mouvements</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Ligne 2 : Tension sectorielle et Commande publique
    col3, col4 = st.columns(2)

    # 3. TENSION SECTORIELLE RÉGIONALE (INSEE - 12 mois)
    with col3:
        ratio = kpi_data.get("ratio_creation_fermeture", 1.0)
        qualification = kpi_data.get("qualification_tension", "Secteur stable")

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-title">Tension Sectorielle</div>
                <div class="kpi-body">
                    <span class="kpi-value-large">{ratio:.2f}</span>
                    <span class="kpi-unit-large">cr/f</span>
                    <span class="badge-dark">{qualification}</span>
                </div>
                <div class="kpi-footer">Ratio NAF / Dép (12m)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. EXPOSITION À LA COMMANDE PUBLIQUE (BOAMP - 12 mois)
    with col4:
        nb_marches = kpi_data.get("nb_marches_boamp", 0)
        profil = kpi_data.get("profil_commande_publique", "Exclusivement privé")

        st.markdown(
            f"""
            <div class="kpi-card-large">
                <div class="kpi-title">Commande Publique</div>
                <div class="kpi-body">
                    <span class="kpi-value-large">{nb_marches}</span>
                    <span class="kpi-unit-large">marchés</span>
                    <span class="badge-dark">{profil}</span>
                </div>
                <div class="kpi-footer">Source : BOAMP (12m)</div>
            </div>
            """,
            unsafe_allow_html=True
        )