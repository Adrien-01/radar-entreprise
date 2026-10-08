import streamlit as st

def afficher_fiche_identite(data: dict):
    """
    Affiche la fiche d'identité administrative et opérationnelle de l'entreprise.
    """
    st.subheader(f"🏢 {data.get('raison_sociale', 'Raison sociale inconnue')}")
    
    # Badge statut administratif (Actif / Inactif)
    statut = data.get("statut_administratif", "Inconnu")
    if statut == "Actif":
        st.caption("🟢 **Entreprise Active**")
    else:
        st.caption("🔴 **Entreprise Inactive / Cessation**")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**SIREN :** `{data.get('siren')}`")
        st.markdown(f"**Date de création :** {data.get('date_creation', 'N/A')}")
        st.markdown(f"**Tranche d'effectifs :** {data.get('tranche_effectifs', 'Non renseigné')}")

    with col2:
        st.markdown(f"**Activité (NAF/APE) :** {data.get('code_naf')} - {data.get('libelle_naf', '')}")
        st.markdown(f"**Adresse du siège :** {data.get('adresse_siege', 'N/A')}")

    with col3:
        st.markdown(f"**Dirigeants / Gouvernance :**")
        st.write(data.get('dirigeants', 'Aucun dirigeant répertorié'))

    st.markdown("---")