SELECT
    CAST(siren AS VARCHAR) AS siren,
    COALESCE(flag_bodacc, 0) AS flag_bodacc,
    COALESCE(procedure_label, 'Aucune procédure détectée') AS procedure_label,
    COALESCE(mouvements_24m, 0) AS mouvements_24m
FROM {{ source('raw', 'raw_bodacc') }}
WHERE siren = '{{ var("target_siren") }}'
