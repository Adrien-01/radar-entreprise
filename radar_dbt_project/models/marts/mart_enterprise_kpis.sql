WITH base AS (
    SELECT * FROM {{ ref('int_entreprise_360') }}
)

SELECT
    siren,
    raison_sociale,
    code_naf,
    section_activite,
    tranche_effectifs,
    statut_administratif,
    adresse_siege,
    dirigeants,
    date_creation,

    -- 1. KPI : Santé Légale (24m)
    flag_bodacc,
    mouvements_24m,
    CASE
        WHEN statut_administratif = 'Inactif' THEN 'CRITIQUE'
        WHEN flag_bodacc = 1 THEN 'EN VIGILANCE'
        ELSE 'SAIN'
    END AS sante_legale_label,

    -- 2. KPI : Gouvernance (24m)
    nb_mouvements_gov,
    CASE
        WHEN nb_mouvements_gov >= 3 THEN 'SIGNAL INSTABILITE'
        ELSE 'STABLE'
    END AS gouvernance_label,

    -- 3. KPI : Ancienneté & Phase de Vie
    DATE_DIFF('year', date_creation, CURRENT_DATE) AS age_entreprise_ans,
    CASE
        WHEN DATE_DIFF('year', date_creation, CURRENT_DATE) < 3 THEN 'Jeune Pousse'
        ELSE 'Entreprise Établie'
    END AS phase_vie_label,

    -- 4. KPI : Performance Financière (remplace la commande publique)
    annee_exercice,
    chiffre_affaires,
    resultat_net,
    marge_nette_pct,
    CASE
        WHEN marge_nette_pct < 1.0 THEN 'MARGE FAIBLE'
        WHEN marge_nette_pct BETWEEN 1.0 AND 3.5 THEN 'MARGE CONFORME'
        ELSE 'FORTE RENTABILITÉ'
    END AS rentabilite_label,

    -- Métriques sectorielles pour les graphiques
    nb_creations_12m,
    nb_fermetures_12m,
    ratio_creation_fermeture

FROM base
