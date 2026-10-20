SELECT
    code_naf,
    departement,
    COALESCE(nb_creations_12m, 0) AS nb_creations_12m,
    COALESCE(nb_fermetures_12m, 0) AS nb_fermetures_12m,
    COALESCE(ratio_creation_fermeture, 1.0) AS ratio_creation_fermeture
FROM {{ source('raw', 'raw_insee_demographie') }}
