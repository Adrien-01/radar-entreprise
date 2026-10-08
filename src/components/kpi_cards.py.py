import streamlit as st

def render_kpi_cards(kpi_data: dict):
    """
    Rend la grille responsive de 4 KPI décisionnels avec badges colorés.
    """
    col1, col2, col3, col4 = st.columns(4)

    # 1. SCORE DE SANTÉ LÉGALE (BODACC - 24 mois)
    with col1:
        flag_bodacc = kpi_data.get("flag_bodacc", 0)
        is_procedure = (flag_bodacc == 1)
        bg_color = "#FEE2E2" if is_procedure else "#DCFCE7"
        text_color = "#991B1B" if is_procedure else "#166534"
        border_color = "#EF4444" if is_procedure else "#22C55E"
        status_label = "1 • PROCÉDURE ACTIVE" if is_procedure else "0 • SAIN"

        st.markdown(
            f"""
            <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 14px; border-radius: 8px; height: 100%;">
                <p style="font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; margin: 0;">Santé Légale (24m)</p>
                <div style="margin-top: 8px;">
                    <span style="background-color: #FFFFFF; color: {text_color}; font-size: 0.75rem; font-weight: 800; padding: 4px 8px; border-radius: 12px; border: 1px solid {border_color};">
                        {status_label}
                    </span>
                </div>
                <p style="font-size: 0.7rem; color: #6B7280; margin-top: 10px; margin-bottom: 0;">Source : BODACC</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. INDICE D'INSTABILITÉ DE LA GOUVERNANCE (24 mois)
    with col2:
        mouvements = kpi_data.get("nb_mouvements_gov", 0)
        is_unstable = (mouvements >= 3)
        badge_bg = "#FEF3C7" if is_unstable else "#F3F4F6"
        badge_text = "#92400E" if is_unstable else "#374151"
        badge_label = "SIGNAL D'INSTABILITÉ" if is_unstable else "STABLE"

        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 14px; border-radius: 8px; height: 100%;">
                <p style="font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; margin: 0;">Gouvernance (24m)</p>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: #111827;">{mouvements} <span style="font-size: 0.75rem; font-weight: 400; color: #6B7280;">mouvt.</span></span>
                    <span style="background-color: {badge_bg}; color: {badge_text}; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 12px;">{badge_label}</span>
                </div>
                <p style="font-size: 0.7rem; color: #9CA3AF; margin-top: 10px; margin-bottom: 0;">Seuil : ≥ 3 mouvements</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3. TENSION SECTORIELLE RÉGIONALE (INSEE - 12 mois)
    with col3:
        ratio = kpi_data.get("ratio_creation_fermeture", 1.0)
        qualification = kpi_data.get("qualification_tension", "Secteur stable")

        color_map = {
            "Secteur dynamique": ("#DCFCE7", "#166534"),
            "Secteur stable": ("#E0F2FE", "#075985"),
            "Secteur sous tension": ("#FFEDD5", "#9A3412")
        }
        b_bg, b_txt = color_map.get(qualification, ("#F3F4F6", "#374151"))

        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 14px; border-radius: 8px; height: 100%;">
                <p style="font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; margin: 0;">Tension Sectorielle</p>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: #111827;">{ratio:.2f} <span style="font-size: 0.75rem; font-weight: 400; color: #6B7280;">cr/f</span></span>
                    <span style="background-color: {b_bg}; color: {b_txt}; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 12px;">{qualification}</span>
                </div>
                <p style="font-size: 0.7rem; color: #9CA3AF; margin-top: 10px; margin-bottom: 0;">Ratio NAF / Dép (12m)</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 4. EXPOSITION À LA COMMANDE PUBLIQUE (BOAMP - 12 mois)
    with col4:
        nb_marches = kpi_data.get("nb_marches_boamp", 0)
        profil = kpi_data.get("profil_commande_publique", "Exclusivement privé")

        prof_map = {
            "Dépendance publique forte": ("#DBEAFE", "#1E40AF"),
            "Diversifié": ("#E0E7FF", "#3730A3"),
            "Exclusivement privé": ("#F3F4F6", "#374151")
        }
        p_bg, p_txt = prof_map.get(profil, ("#F3F4F6", "#374151"))

        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; padding: 14px; border-radius: 8px; height: 100%;">
                <p style="font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; margin: 0;">Commande Publique</p>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
                    <span style="font-size: 1.4rem; font-weight: 800; color: #111827;">{nb_marches} <span style="font-size: 0.75rem; font-weight: 400; color: #6B7280;">marchés</span></span>
                    <span style="background-color: {p_bg}; color: {p_txt}; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 12px;">{profil}</span>
                </div>
                <p style="font-size: 0.7rem; color: #9CA3AF; margin-top: 10px; margin-bottom: 0;">Source : BOAMP (12m)</p>
            </div>
            """,
            unsafe_allow_html=True
        )