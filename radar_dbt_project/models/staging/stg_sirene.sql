SELECT
    CAST(siren AS VARCHAR) AS siren,
    UPPER(TRIM(raison_sociale)) AS raison_sociale,
    statut_administratif,
    CAST(date_creation AS DATE) AS date_creation,
    tranche_effectifs,
    code_naf,
    section_activite,
    departement,
    adresse_siege,
    dirigeants,
    COALESCE(nb_mouvements_gov, 0) AS nb_mouvements_gov
FROM {{ source('raw', 'raw_sirene') }}
WHERE siren = '{{ var("target_siren") }}'
