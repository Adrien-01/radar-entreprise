WITH sirene AS (
    SELECT * FROM {{ ref('stg_sirene') }}
),
bodacc AS (
    SELECT * FROM {{ ref('stg_bodacc') }}
),
finances AS (
    SELECT * FROM {{ ref('stg_finances') }}
),
insee AS (
    SELECT * FROM {{ ref('stg_insee_demographie') }}
)

SELECT
    s.*,

    -- 1. Santé Légale & Activité (BODACC - 24 mois)
    COALESCE(b.flag_bodacc, 0) AS flag_bodacc,
    COALESCE(b.procedure_label, 'Aucune procédure détectée') AS procedure_label,
    COALESCE(b.mouvements_24m, 0) AS mouvements_24m,

    -- Étiquette Santé Légale
    CASE
        WHEN s.statut_administratif = 'Inactif' THEN 'CRITIQUE'
        WHEN COALESCE(b.flag_bodacc, 0) = 1 THEN 'EN VIGILANCE'
        ELSE 'SAIN'
    END AS sante_legale_label,

    -- Étiquette Gouvernance (Seuil à 3 mouvements sur 24m)
    CASE
        WHEN COALESCE(s.nb_mouvements_gov, 0) >= 3 THEN 'INSTABLE'
        ELSE 'STABLE'
    END AS gouvernance_statut,

    -- 2. Performance Financière
    f.annee AS annee_exercice,
    f.chiffre_affaires,
    f.resultat_net,
    f.marge_nette_pct,

    -- 3. Démographie sectorielle (INSEE)
    i.nb_creations_12m,
    i.nb_fermetures_12m,
    i.ratio_creation_fermeture

FROM sirene s
LEFT JOIN bodacc b ON s.siren = b.siren
LEFT JOIN finances f ON s.siren = f.siren
LEFT JOIN insee i ON s.code_naf = i.code_naf AND s.departement = i.departement
