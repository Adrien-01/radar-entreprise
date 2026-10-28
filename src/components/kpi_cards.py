import streamlit as st

def render_kpi_cards(kpi_data: dict):
    """
    Rend une grille de 4 KPI décisionnels au format 2x2 avec un style graphique propre,
    intégrant l'intitulé et les mouvements de santé légale (BODACC - 24m).
    """
    # Ligne 1 : Santé légale et Gouvernance
    col1, col2 = st.columns(2)

    # 1. SCORE DE SANTÉ LÉGALE & ACTIVITÉ (BODACC - 24 mois)
    with col1:
        flag_bodacc = kpi_data.get("flag_bodacc", 0)
        procedure_label = kpi_data.get("procedure_label", "Aucune procédure détectée")

        # Récupération sécurisée du nombre de mouvements sur 24 mois
        mouvements_24m = kpi_data.get("mouvements_24m", kpi_data.get("nb_mouvements_gov", 0))

        is_procedure = (flag_bodacc == 1)

        # Logique d'affichage et de seuils
        if is_procedure:
            status_label = "1 • PROCÉDURE ACTIVE"
            badge_class = "badge-red"
        elif mouvements_24m >= 5:
            # Exemple de seuil personnalisé pour notifier une forte activité légale/mouvements
            status_label = f"SAIN ({mouvements_24m} mouvts)"
            badge_class = "badge-dark"
        else:
            status_label = "0 • SAIN"
            badge_class = "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large" style="padding: 16px;">
                <div class="kpi-title">Santé Légale & Activité (24m)</div>
                <div class="kpi-body" style="margin-top: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <span class="{badge_class}" style="font-size: 0.9rem; padding: 5px 10px; font-weight: bold;">{status_label}</span>
                    <span style="font-size: 1rem; font-weight: 600; color: #e0e0e0;">{mouvements_24m} mouvt{'s' if mouvements_24m > 1 else ''}</span>
                </div>
                <div style="margin-top: 10px; font-size: 0.85rem; color: {'#ff6b6b' if is_procedure else '#4cd137'};">
                    <strong>Intitulé :</strong> {procedure_label}
                </div>
                <div class="kpi-footer" style="margin-top: 10px;">Source : BODACC</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. INDICE D'INSTABILITÉ DE LA GOUVERNANCE (24 mois)
    with col2:
        mouvements = kpi_data.get("nb_mouvements_gov", kpi_data.get("mouvements_24m", 0))
        is_unstable = (mouvements >= 3)
        badge_label = "SIGNAL D'INSTABILITÉ" if is_unstable else "STABLE"
        badge_class = "badge-red" if is_unstable else "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large" style="padding: 16px;">
                <div class="kpi-title">Gouvernance (24m)</div>
                <div class="kpi-body" style="margin-top: 5px;">
                    <span class="kpi-value-large">{mouvements}</span>
                    <span class="kpi-unit-large">mouvt.</span>
                    <div style="margin-top: 8px;">
                        <span class="{badge_class}" style="font-size: 0.85rem; padding: 4px 8px;">{badge_label}</span>
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
            <div class="kpi-card-large" style="padding: 16px;">
                <div class="kpi-title">Tension Sectorielle</div>
                <div class="kpi-body" style="margin-top: 5px;">
                    <span class="kpi-value-large">{ratio:.2f}</span>
                    <span class="kpi-unit-large">cr/f</span>
                    <div style="margin-top: 8px;">
                        <span class="badge-dark" style="font-size: 0.85rem; padding: 4px 8px;">{qualification}</span>
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
        annee = kpi_data.get("annee_exercice", "N/A")

        ca_formatted = f"{ca:,.0f} €".replace(",", " ") if ca is not None else "N/A"
        res_formatted = f"{resultat:,.0f} €".replace(",", " ") if resultat is not None else "N/A"
        marge_formatted = f"{marge:.1f}%" if marge is not None else "N/A"

        marge_badge_class = "badge-red" if (marge is not None and marge < 1.0) else "badge-dark"

        st.markdown(
            f"""
            <div class="kpi-card-large" style="padding: 16px;">
                <div class="kpi-title">Performance Financière ({annee})</div>
                <div class="kpi-body" style="margin-top: 5px; font-size: 0.9rem; line-height: 1.5;">
                    <div><b>CA :</b> {ca_formatted}</div>
                    <div><b>Résultat Net :</b> {res_formatted}</div>
                    <div style="margin-top: 4px;"><b>Marge Nette :</b> <span class="{marge_badge_class}" style="font-size: 0.9rem; padding: 3px 8px; font-weight: bold;">{marge_formatted}</span></div>
                </div>
                <div class="kpi-footer" style="margin-top: 8px;">Source : API Recherche Entreprises</div>
            </div>
            """,
            unsafe_allow_html=True
        )
