import requests
import duckdb
from typing import Dict, Any

def fetch_sirene_data(siren: str) -> Dict[str, Any]:
    """
    Interroge l'API Recherche Entreprises (Insee / Etalab) pour récupérer les données administratives réelles.
    Lève une exception si l'entreprise n'est pas trouvée.
    """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}"
    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        raise ConnectionError(f"Erreur HTTP lors de l'accès à l'API Sirene (Code : {response.status_code})")

    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"Aucune entreprise enregistrée pour le SIREN : {siren}")

    company = results[0]
    siege = company.get("siege", {})

    # Formatage de l'adresse du siège
    adresse_parts = [
        siege.get("numero_voie"),
        siege.get("indice_repetition"),
        siege.get("type_voie"),
        siege.get("libelle_voie"),
        siege.get("code_postal"),
        siege.get("libelle_commune")
    ]
    adresse_siege = " ".join([str(p) for p in adresse_parts if p]) or "N/A"

    return {
        "siren": company.get("siren", siren),
        "raison_sociale": company.get("nom_complet", "ENTREPRISE INCONNUE"),
        "statut_administratif": "Actif" if company.get("etat_administratif") == "A" else "Inactif",
        "date_creation": company.get("date_creation", "N/A"),
        "tranche_effectifs": company.get("tranche_effectifs_salarie", "Non renseigné"),
        "code_naf": company.get("activite_principale", "N/A"),
        "libelle_naf": company.get("libelle_activite_principale", "N/A"),
        "departement": siege.get("departement", "44"),
        "adresse_siege": adresse_siege,
        "dirigeants": ",. ".join([f"{d.get('prenoms', '')} {d.get('nom', '')}" for d in company.get("dirigeants", [])]) or "Aucun dirigeant répertorié",
        "nb_mouvements_gov": len(company.get("dirigeants", []))
    }


def fetch_bodacc_data(siren: str) -> Dict[str, Any]:
    """
    Interroge l'API BODACC (via OpenDataSoft) pour détecter d'éventuelles procédures collectives.
    """
    url = f"https://bodacc-dataservice.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=siren%3D%22{siren}%22&limit=20"
    has_procedure = 0
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            annonces = response.json().get("results", [])
            for annonce in annonces:
                famille = str(annonce.get("familleavis", "")).lower()
                if "liquidation" in famille or "redressement" in famille or "sauvegarde" in famille:
                    has_procedure = 1
                    break
    except Exception as e:
        print(f"[API BODACC Error] {e}")

    return {
        "siren": siren,
        "flag_bodacc": has_procedure
    }


def fetch_boamp_data(siren: str) -> Dict[str, Any]:
    """
    Interroge l'API BOAMP pour mesurer le nombre de marchés publics remportés.
    """
    url = f"https://dila-api.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records?where=siren%3D%22{siren}%22&limit=1"
    nb_marches = 0
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            nb_marches = response.json().get("total_count", 0)
    except Exception as e:
        print(f"[API BOAMP Error] {e}")

    profil = "Dépendance publique forte" if nb_marches > 0 else "Exclusivement privé"

    return {
        "siren": siren,
        "nb_marches_boamp": nb_marches,
        "profil_commande_publique": profil
    }


def ingest_siren_data_to_duckdb(siren: str, conn: duckdb.DuckDBPyConnection):
    """
    Ingère l'ensemble des réponses API brutes dans les tables Staging DuckDB.
    """
    sirene_data = fetch_sirene_data(siren)  # Lèvera une erreur si le SIREN n'existe pas
    bodacc_data = fetch_bodacc_data(siren)
    boamp_data = fetch_boamp_data(siren)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_sirene (
            siren VARCHAR,
            raison_sociale VARCHAR,
            statut_administratif VARCHAR,
            date_creation VARCHAR,
            tranche_effectifs VARCHAR,
            code_naf VARCHAR,
            libelle_naf VARCHAR,
            departement VARCHAR,
            adresse_siege VARCHAR,
            dirigeants VARCHAR,
            nb_mouvements_gov INTEGER
        );
        CREATE TABLE IF NOT EXISTS raw_bodacc (
            siren VARCHAR,
            flag_bodacc INTEGER
        );
        CREATE TABLE IF NOT EXISTS raw_boamp (
            siren VARCHAR,
            nb_marches_boamp INTEGER,
            profil_commande_publique VARCHAR
        );
    """)

    # Nettoyage des anciennes entrées
    conn.execute("DELETE FROM raw_sirene WHERE siren = ?", [siren])
    conn.execute("DELETE FROM raw_bodacc WHERE siren = ?", [siren])
    conn.execute("DELETE FROM raw_boamp WHERE siren = ?", [siren])

    # Insertion des nouvelles données
    conn.execute("INSERT INTO raw_sirene VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        sirene_data["siren"],
        sirene_data["raison_sociale"],
        sirene_data["statut_administratif"],
        sirene_data["date_creation"],
        sirene_data["tranche_effectifs"],
        sirene_data["code_naf"],
        sirene_data["libelle_naf"],
        sirene_data["departement"],
        sirene_data["adresse_siege"],
        sirene_data["dirigeants"],
        sirene_data["nb_mouvements_gov"]
    ])

    conn.execute("INSERT INTO raw_bodacc VALUES (?, ?)", [
        bodacc_data["siren"],
        bodacc_data["flag_bodacc"]
    ])

    conn.execute("INSERT INTO raw_boamp VALUES (?, ?, ?)", [
        boamp_data["siren"],
        boamp_data["nb_marches_boamp"],
        boamp_data["profil_commande_publique"]
    ])
