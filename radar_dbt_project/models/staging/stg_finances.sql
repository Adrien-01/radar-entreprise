SELECT
    CAST(siren AS VARCHAR) AS siren,
    CAST(annee AS INTEGER) AS annee,
    COALESCE(chiffre_affaires, 0) AS chiffre_affaires,
    COALESCE(resultat_net, 0) AS resultat_net,
    COALESCE(marge_nette_pct, 0.0) AS marge_nette_pct
FROM {{ source('raw', 'raw_finances') }}
WHERE siren = '{{ var("target_siren") }}'
