from typing import Any

import duckdb
import requests

# 1. Dictionnaire officiel des sections NAF (Rév. 2)
NAF_SECTIONS = {
    "A": "Agriculture, sylviculture et pêche",
    "B": "Industries extractives",
    "C": "Industrie manufacturière",
    "D": (
        "Production et distribution d'électricité, de gaz, de vapeur et d'air"
        " conditionné"
    ),
    "E": (
        "Production et distribution d'eau ; assainissement, gestion des"
        " déchets et dépollution"
    ),
    "F": "Construction",
    "G": "Commerce ; réparation d'automobiles et de motocycles",
    "H": "Transports et entreposage",
    "I": "Hébergement et restauration",
    "J": "Information et communication",
    "K": "Activités financières et d'assurance",
    "L": "Activités immobilières",
    "M": "Activités spécialisées, scientifiques et techniques",
    "N": "Activités de services administratifs et de soutien",
    "O": "Administration publique",
    "P": "Enseignement",
    "Q": "Santé humaine et action sociale",
    "R": "Arts, spectacles et activités récréatives",
    "S": "Autres activités de services",
    "T": (
        "Activités des ménages en tant qu'employeurs ; activités"
        " indifférenciées des ménages en tant que producteurs de biens et"
        " services pour usage propre"
    ),
    "U": "Activités extra-territoriales",
}

# 2. Dictionnaire officiel des tranches d'effectifs INSEE
TRANCHES_EFFECTIFS = {
    "00": "0 salarié (ayant employé des salariés)",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1 000 à 1 999 salariés",
    "51": "2 000 à 4 999 salariés",
    "52": "5 000 à 9 999 salariés",
    "53": "10 000 salariés et plus",
    "NN": "Unités non employeuses",
}


def fetch_sirene_data(siren: str) -> dict[str, Any]:
  """Interroge l'API Recherche Entreprises (Insee / Etalab) pour récupérer les données administratives réelles.

  Lève une exception si l'entreprise n'est pas trouvée.
  """
  url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}"
  response = requests.get(url, timeout=5)

  if response.status_code != 200:
    raise ConnectionError(
        f"Erreur HTTP lors de l'accès à l'API Sirene (Code :"
        f" {response.status_code})"
    )

  results = response.json().get("results", [])
  if not results:
    raise ValueError(f"Aucune entreprise enregistrée pour le SIREN : {siren}")

  company = results[0]
  siege = company.get("siege", {})

  # Formatage propre de l'adresse du siège
  adresse_parts = [
      siege.get("numero_voie"),
      siege.get("indice_repetition"),
      siege.get("type_voie"),
      siege.get("libelle_voie"),
      siege.get("code_postal"),
      siege.get("libelle_commune"),
  ]
  adresse_siege = " ".join([str(p) for p in adresse_parts if p]) or "N/A"

  # Nettoyage et filtrage des dirigeants valides
  dirigeants_clean = []
  for d in company.get("dirigeants", []):
    prenom = d.get("prenoms", "") or ""
    nom = d.get("nom", "") or ""
    full_name = f"{prenom} {nom}".strip()
    if full_name:
      dirigeants_clean.append(full_name)

  # Conversion Section NAF
  section_lettre = company.get("section_activite_principale", "N/A")
  section_libelle = NAF_SECTIONS.get(section_lettre, section_lettre)

  # Conversion Tranche d'effectifs
  code_tranche = (
      company.get("tranche_effectif_salarie")
      or company.get("tranche_effectifs_salarie")
      or company.get("tranche_effectifs")
      or siege.get("tranche_effectif_salarie")
      or "Non renseigné"
  )
  tranche_libelle = TRANCHES_EFFECTIFS.get(code_tranche, code_tranche)

  # Statut administratif enrichi
  etat_brut = company.get("etat_administratif", "A")
  date_cessation = company.get("date_cessation")

  if etat_brut == "A":
    if date_cessation:
      statut_detaille = (
          f"En cours de cessation (Date enregistrée : {date_cessation})"
      )
    else:
      statut_detaille = "Actif"
  else:
    statut_detaille = f"Cessé ou Radié (Code INSEE : {etat_brut})"

  return {
      "siren": company.get("siren", siren),
      "raison_sociale": company.get("nom_complet", "ENTREPRISE INCONNUE"),
      "statut_administratif": statut_detaille,
      "date_creation": company.get("date_creation", "N/A"),
      "tranche_effectifs": tranche_libelle,
      "section_activite": section_libelle,
      "code_naf": company.get("activite_principale", "N/A"),
      "departement": siege.get("departement", "44"),
      "adresse_siege": adresse_siege,
      "dirigeants": ", ".join(dirigeants_clean) or "Aucun dirigeant répertorié",
      "nb_mouvements_gov": len(dirigeants_clean),
  }


import json
from datetime import datetime, timedelta
from typing import Any


def fetch_bodacc_analytics(siren: str) -> dict[str, Any]:
    """
    Interroge l'API BODACC, filtre les annonces des 24 derniers mois,
    compte les mouvements et détecte les procédures (sans stocker le brut).
    """
    url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=registre%3D%22{siren}%22&limit=50"

    has_procedure = 0
    procedure_label = "Aucune procédure détectée"
    mouvements_24m = 0

    # Seuil des 24 derniers mois
    date_limite_24m = datetime.now() - timedelta(days=730)

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data_json = response.json()
            annonces = data_json.get("results", [])

            for annonce in annonces:
                date_parution_str = annonce.get("dateparution")
                if date_parution_str:
                    try:
                        date_annonce = datetime.fromisoformat(date_parution_str.split("T")[0])

                        # Filtrer uniquement les 24 derniers mois
                        if date_annonce >= date_limite_24m:
                            mouvements_24m += 1

                            # Recherche de la procédure collective et de son intitulé
                            texte_annonce = json.dumps(annonce, ensure_ascii=False).lower()

                            if "liquidation" in texte_annonce:
                                has_procedure = 1
                                procedure_label = "Liquidation judiciaire"
                            elif "redressement" in texte_annonce and has_procedure == 0:
                                has_procedure = 1
                                procedure_label = "Redressement judiciaire"
                            elif "sauvegarde" in texte_annonce and has_procedure == 0:
                                has_procedure = 1
                                procedure_label = "Procédure de sauvegarde"
                    except (KeyError, TypeError, ValueError):
                      continue
    except Exception as e: # noqa:BLE001
        print(f"❌ [API BODACC Error] {e}")

    return {
        "siren": siren,
        "flag_bodacc": has_procedure,
        "procedure_label": procedure_label,
        "mouvements_24m": mouvements_24m
    }


def get_financial_history(siren: str) -> dict[str, Any]:
    """
    Extrait l'historique financier pluriannuel disponible et calcule la marge nette %.
    """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siren}"
    print(f"\n[FINANCES] 🔍 Récupération de l'historique financier pour le SIREN : {siren}")

    historique_detaille = []

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if results:
                company = results[0]
                finances = company.get("finances", {})

                if finances:
                    annees_triees = sorted([str(an) for an in finances.keys()])

                    for annee in annees_triees:
                        donnees_annee = finances[annee]
                        ca = donnees_annee.get("ca")
                        resultat_net = donnees_annee.get("resultat_net")

                        # Calcul de la marge nette en %
                        marge_nette_pct = None
                        if ca and resultat_net is not None and ca != 0:
                            marge_nette_pct = round((resultat_net / ca) * 100, 2)

                        historique_detaille.append({
                            "annee": int(annee),
                            "chiffre_affaires": ca,
                            "resultat_net": resultat_net,
                            "marge_nette_pct": marge_nette_pct
                        })
                else:
                    print("[FINANCES] ⚠️ Aucune donnée financière disponible dans l'API.")
            else:
                print("[FINANCES] ❌ Entreprise non trouvée.")
        else:
            print(f"[FINANCES] ❌ Erreur API (Code {response.status_code})")

    except Exception as e: # noqa:BLE001
        print(f"[FINANCES] ❌ [API Finances Error] {e}")

    return {
        "siren": siren,
        "historique": historique_detaille
    }


def fetch_insee_sector_demography(code_naf: str, departement: str) -> dict:
    if "." not in code_naf and len(code_naf) >= 4:
        clean_naf = f"{code_naf[:2]}.{code_naf[2:]}"
    else:
        clean_naf = code_naf

    clean_dept = str(departement).zfill(2) if str(departement).isdigit() else str(departement)

    creations_count = 0
    fermetures_count = 0

    try:
        # 1. Entreprises actives (Créations / Actives)
        url_actifs = f"https://recherche-entreprises.api.gouv.fr/search?activite_principale={clean_naf}&departement={clean_dept}&etat_administratif=A&per_page=1"
        resp_actifs = requests.get(url_actifs, timeout=5)
        if resp_actifs.status_code == 200:
            data_actifs = resp_actifs.json()
            creations_count = data_actifs.get("total_results", 0)

            # Fallback département seul si 0 résultat strict
            if creations_count == 0:
                url_actifs_elargi = f"https://recherche-entreprises.api.gouv.fr/search?departement={clean_dept}&etat_administratif=A&per_page=1"
                resp_AE = requests.get(url_actifs_elargi, timeout=5)
                if resp_AE.status_code == 200:
                    creations_count = resp_AE.json().get("total_results", 0)

        # 2. Entreprises cessées (Fermetures)
        url_cesses = f"https://recherche-entreprises.api.gouv.fr/search?activite_principale={clean_naf}&departement={clean_dept}&etat_administratif=C&per_page=1"
        resp_cesses = requests.get(url_cesses, timeout=5)
        if resp_cesses.status_code == 200:
            data_cesses = resp_cesses.json()
            fermetures_count = data_cesses.get("total_results", 0)

            # Fallback département seul si 0 résultat strict
            if fermetures_count == 0:
                url_cesses_elargi = f"https://recherche-entreprises.api.gouv.fr/search?departement={clean_dept}&etat_administratif=C&per_page=1"
                resp_CE = requests.get(url_cesses_elargi, timeout=5)
                if resp_CE.status_code == 200:
                    fermetures_count = resp_CE.json().get("total_results", 0)

    except Exception as e: # noqa:BLE001
        print(f"[API INSEE Démographie Error] {e}")

    ratio = round(creations_count / max(fermetures_count, 1), 2)

    return {
        "code_naf": clean_naf,
        "departement": clean_dept,
        "nb_creations_12m": creations_count,
        "nb_fermetures_12m": fermetures_count,
        "ratio_creation_fermeture": ratio
    }


def ingest_siren_data_to_duckdb(siren: str, conn: duckdb.DuckDBPyConnection):
    """
    Ingère l'ensemble des réponses API brutes dans les tables Staging DuckDB.
    """
    sirene_data = fetch_sirene_data(siren)  # Lèvera une erreur si le SIREN n'existe pas
    bodacc_data = fetch_bodacc_analytics(siren)
    financial_data = get_financial_history(siren)

    # Récupération des données sectorielles INSEE basées sur le NAF et le département de l'entreprise
    insee_data = fetch_insee_sector_demography(sirene_data["code_naf"], sirene_data["departement"])

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_sirene (
            siren VARCHAR,
            raison_sociale VARCHAR,
            statut_administratif VARCHAR,
            date_creation VARCHAR,
            tranche_effectifs VARCHAR,
            code_naf VARCHAR,
            section_activite VARCHAR,
            departement VARCHAR,
            adresse_siege VARCHAR,
            dirigeants VARCHAR,
            nb_mouvements_gov INTEGER
        );
        CREATE TABLE IF NOT EXISTS raw_bodacc (
            siren VARCHAR,
            flag_bodacc INTEGER,
            procedure_label VARCHAR,
            mouvements_24m INTEGER
        );
        CREATE TABLE IF NOT EXISTS raw_finances (
            siren VARCHAR,
            annee INTEGER,
            chiffre_affaires BIGINT,
            resultat_net BIGINT,
            marge_nette_pct DOUBLE
        );
        CREATE TABLE IF NOT EXISTS raw_insee_demographie (
            code_naf VARCHAR,
            departement VARCHAR,
            nb_creations_12m INTEGER,
            nb_fermetures_12m INTEGER,
            ratio_creation_fermeture DOUBLE
        );
    """)

    # Nettoyage des anciennes entrées
    conn.execute("DELETE FROM raw_sirene WHERE siren = ?", [siren])
    conn.execute("DELETE FROM raw_bodacc WHERE siren = ?", [siren])
    conn.execute("DELETE FROM raw_finances WHERE siren = ?", [siren])
    conn.execute("DELETE FROM raw_insee_demographie WHERE code_naf = ? AND departement = ?", [sirene_data["code_naf"], sirene_data["departement"]])

    # Insertion des nouvelles données
    conn.execute("INSERT INTO raw_sirene VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        sirene_data["siren"],
        sirene_data["raison_sociale"],
        sirene_data["statut_administratif"],
        sirene_data["date_creation"],
        sirene_data["tranche_effectifs"],
        sirene_data["code_naf"],
        sirene_data["section_activite"],
        sirene_data["departement"],
        sirene_data["adresse_siege"],
        sirene_data["dirigeants"],
        sirene_data["nb_mouvements_gov"]
    ])

    # Correction ici : 4 placeholders (?, ?, ?, ?) au lieu de 3
    conn.execute("INSERT INTO raw_bodacc VALUES (?, ?, ?, ?)", [
        bodacc_data["siren"],
        bodacc_data["flag_bodacc"],
        bodacc_data["procedure_label"],
        bodacc_data["mouvements_24m"]
    ])

    # Insertion des lignes de l'historique financier sans les évolutions en %
    for item in financial_data["historique"]:
        conn.execute("INSERT INTO raw_finances VALUES (?, ?, ?, ?, ?)", [
            siren,
            item["annee"],
            item["chiffre_affaires"],
            item["resultat_net"],
            item["marge_nette_pct"]
        ])

    conn.execute("INSERT INTO raw_insee_demographie VALUES (?, ?, ?, ?, ?)", [
        insee_data["code_naf"],
        insee_data["departement"],
        insee_data["nb_creations_12m"],
        insee_data["nb_fermetures_12m"],
        insee_data["ratio_creation_fermeture"]
    ])
