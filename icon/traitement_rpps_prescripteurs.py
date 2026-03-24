# traitement_rpps_prescripteurs.py
#
# Script de traitement des trois fichiers RPPS de l'ANS
# Source : https://www.data.gouv.fr/datasets/annuaire-sante-...
# Documentation officielle : DSFT Annuaire Santé v3.1 (ANS)
#
# Perimetre retenu : medecins, chirurgiens-dentistes, sages-femmes
# car ce sont les seuls habilites a prescrire un arret maladie
#
# Fichiers en entree :
#   - PS_LibreAcces_Personne_activite_[Date].txt  (761 Mo)
#   - PS_LibreAcces_Dipl_AutExerc_[Date].txt      (258 Mo)
#   - PS_LibreAcces_SavoirFaire_[Date].txt         (49 Mo)
#
# Format : UTF-8, separateur |, une ligne d'entete, pas de guillemets
#
# Sortie : table PostgreSQL referentiels.prescripteurs_autorises

import pandas as pd
import numpy as np
from pathlib import Path
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------
# CONSTANTES METIER
# --------------------------------------------------------------------

# Codes professions issus de la TRE_R94 de l'ANS
# Seules ces trois professions sont habilitees a prescrire un arret maladie
PROFESSIONS_PRESCRIPTEURS = {
    "10": "Medecin",
    "40": "Chirurgien-Dentiste",
    "60": "Sage-Femme",
}

# Colonnes a conserver dans PS_LibreAcces_Personne_activite
# selon la documentation DSFT v3.1
COLONNES_PERSONNE = {
    "Identifiant_PP":                       "rpps",
    "Civilite_Exercice":                    "civilite",
    "Nom_Exercice":                         "nom_exercice",
    "Prenom_Exercice":                      "prenom_exercice",
    "Code_Profession":                      "code_profession",
    "Libelle_Profession":                   "libelle_profession",
    "Code_Categorie_Professionnelle":       "code_categorie",
    "Libelle_Categorie_Professionnelle":    "libelle_categorie",
    "Code_Type_Savoir_Faire":               "code_type_savoir_faire",
    "Libelle_Type_Savoir_Faire":            "libelle_type_savoir_faire",
    "Code_Savoir_Faire":                    "code_savoir_faire",
    "Libelle_Savoir_Faire":                 "libelle_savoir_faire",
    "Code_Mode_Exercice":                   "code_mode_exercice",
    "Libelle_Mode_Exercice":                "libelle_mode_exercice",
    "Code_Section_Tableau_Pharmaciens":     "code_section_tableau",
    "Libelle_Section_Tableau_Pharmaciens":  "libelle_section_tableau",
    "Code_Role":                            "code_role",
    "Libelle_Role":                         "libelle_role",
    "Numero_SIRET_Site":                    "siret_site",
    "Numero_FINESS_Site":                   "finess_site",
    "Numero_FINESS_Etablissement_juridique":"finess_ej",
    "Identifiant_Technique_Structure":      "id_technique_structure",
    "Raison_Sociale_Site":                  "raison_sociale_site",
    "Enseigne_Commerciale_Site":            "enseigne_site",
    "Complement_Destinataire":              "complement_destinataire",
    "Complement_Point_Geographique":        "complement_geo",
    "Numero_Voie":                          "numero_voie",
    "Indice_Repetition_Voie":               "indice_repetition",
    "Code_Type_Voie":                       "code_type_voie",
    "Libelle_Type_Voie":                    "libelle_type_voie",
    "Libelle_Voie":                         "libelle_voie",
    "Mention_Distribution":                 "mention_distribution",
    "Bureau_Cedex":                         "bureau_cedex",
    "Code_Postal":                          "code_postal",
    "Code_Commune":                         "code_commune",
    "Libelle_Commune":                      "libelle_commune",
    "Code_Pays":                            "code_pays",
    "Libelle_Pays":                         "libelle_pays",
    "Telephone":                            "telephone",
    "Telephone_2":                          "telephone_2",
    "Telecopie":                            "telecopie",
    "Code_Departement":                     "code_departement",
    "Libelle_Departement":                  "libelle_departement",
    "Code_Genre_Activite":                  "code_genre_activite",
    "Libelle_Genre_Activite":               "libelle_genre_activite",
    "Code_Secteur_Activite":                "code_secteur_activite",
    "Libelle_Secteur_Activite":             "libelle_secteur_activite",
}

# Colonnes a conserver dans PS_LibreAcces_Dipl_AutExerc
COLONNES_DIPLOMES = {
    "Identifiant_PP":               "rpps",
    "Code_Diplome":                 "code_diplome",
    "Libelle_Diplome":              "libelle_diplome",
    "Code_Type_Diplome":            "code_type_diplome",
    "Libelle_Type_Diplome":         "libelle_type_diplome",
    "Numero_Diplome":               "numero_diplome",
    "Date_Obtention_Diplome":       "date_obtention_diplome",
    "Code_Categorie_Diplome":       "code_categorie_diplome",
    "Libelle_Categorie_Diplome":    "libelle_categorie_diplome",
}

# Colonnes a conserver dans PS_LibreAcces_SavoirFaire
COLONNES_SAVOIR_FAIRE = {
    "Identifiant_PP":               "rpps",
    "Code_Type_Savoir_Faire":       "code_type_sf",
    "Libelle_Type_Savoir_Faire":    "libelle_type_sf",
    "Code_Savoir_Faire":            "code_sf",
    "Libelle_Savoir_Faire":         "libelle_sf",
}


# --------------------------------------------------------------------
# CONNEXION POSTGRESQL
# --------------------------------------------------------------------

def get_engine():
    url = (
        f"postgresql://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url, echo=False)


# --------------------------------------------------------------------
# ETAPE 1 — TRAITEMENT DE PS_LibreAcces_Personne_activite
# --------------------------------------------------------------------

def traiter_personne_activite(chemin_fichier):
    """
    Lit le fichier principal PS_LibreAcces_Personne_activite.
    Filtre sur les medecins (10), chirurgiens-dentistes (40)
    et sages-femmes (60) uniquement.

    Attention : un meme RPPS peut apparaitre sur plusieurs lignes
    car chaque ligne = une situation d'exercice (activite).
    On conserve toutes les lignes pour avoir toutes les structures
    d'exercice, on dedupliquera plus tard selon le besoin.
    """
    print(f"\n[1/3] Traitement PS_LibreAcces_Personne_activite")
    print(f"Fichier : {chemin_fichier}")
    print(f"Professions retenues : medecins (10), dentistes (40), sages-femmes (60)")

    chunks_filtres = []
    total_brut = 0
    total_filtre = 0

    # Lecture par chunks car le fichier fait 761 Mo
    for chunk in pd.read_csv(
        chemin_fichier,
        sep="|",
        encoding="utf-8",
        chunksize=50_000,
        low_memory=False,
        dtype=str,
        na_values=[""],
        keep_default_na=False,
    ):
        total_brut += len(chunk)

        # Normaliser les noms de colonnes (enlever espaces, casse uniforme)
        chunk.columns = chunk.columns.str.strip()

        # Filtrer sur les professions prescripteurs AAT
        if "Code_Profession" in chunk.columns:
            masque = chunk["Code_Profession"].isin(PROFESSIONS_PRESCRIPTEURS.keys())
            chunk_filtre = chunk[masque].copy()
        else:
            print(f"ATTENTION : colonne Code_Profession absente. Colonnes : {chunk.columns.tolist()[:10]}")
            chunk_filtre = chunk.copy()

        # Garder uniquement les colonnes utiles
        cols_disponibles = {
            k: v for k, v in COLONNES_PERSONNE.items()
            if k in chunk_filtre.columns
        }
        chunk_filtre = chunk_filtre[list(cols_disponibles.keys())].rename(
            columns=cols_disponibles
        )

        total_filtre += len(chunk_filtre)
        chunks_filtres.append(chunk_filtre)

        # Affichage progression
        if total_brut % 500_000 == 0:
            print(f"  Lignes lues : {total_brut:,} | Retenues : {total_filtre:,}")

    df = pd.concat(chunks_filtres, ignore_index=True)

    print(f"\nResultat :")
    print(f"  Lignes brutes lues    : {total_brut:,}")
    print(f"  Lignes retenues       : {total_filtre:,}")
    print(f"  RPPS distincts        : {df['rpps'].nunique():,}")

    if "code_profession" in df.columns:
        print(f"\n  Repartition par profession :")
        for code, libelle in PROFESSIONS_PRESCRIPTEURS.items():
            n = (df["code_profession"] == code).sum()
            print(f"    {libelle} ({code}) : {n:,} situations d'exercice")

    return df


# --------------------------------------------------------------------
# ETAPE 2 — TRAITEMENT DE PS_LibreAcces_Dipl_AutExerc
# --------------------------------------------------------------------

def traiter_diplomes(chemin_fichier, rpps_valides):
    """
    Lit le fichier des diplomes et autorisations d'exercice.
    Filtre pour ne garder que les RPPS des prescripteurs retenus.

    rpps_valides : set des RPPS a conserver (issus de l'etape 1)
    """
    print(f"\n[2/3] Traitement PS_LibreAcces_Dipl_AutExerc")
    print(f"Fichier : {chemin_fichier}")
    print(f"Filtrage sur {len(rpps_valides):,} RPPS retenus a l'etape 1")

    chunks_filtres = []
    total_brut = 0

    for chunk in pd.read_csv(
        chemin_fichier,
        sep="|",
        encoding="utf-8",
        chunksize=50_000,
        low_memory=False,
        dtype=str,
        na_values=[""],
        keep_default_na=False,
    ):
        total_brut += len(chunk)
        chunk.columns = chunk.columns.str.strip()

        if "Identifiant_PP" in chunk.columns:
            masque = chunk["Identifiant_PP"].isin(rpps_valides)
            chunk_filtre = chunk[masque].copy()
        else:
            chunk_filtre = chunk.copy()

        cols_disponibles = {
            k: v for k, v in COLONNES_DIPLOMES.items()
            if k in chunk_filtre.columns
        }
        chunk_filtre = chunk_filtre[list(cols_disponibles.keys())].rename(
            columns=cols_disponibles
        )

        chunks_filtres.append(chunk_filtre)

    df = pd.concat(chunks_filtres, ignore_index=True)

    print(f"  Lignes brutes lues    : {total_brut:,}")
    print(f"  Lignes retenues       : {len(df):,}")
    print(f"  RPPS avec diplome     : {df['rpps'].nunique():,}")

    return df


# --------------------------------------------------------------------
# ETAPE 3 — TRAITEMENT DE PS_LibreAcces_SavoirFaire
# --------------------------------------------------------------------

def traiter_savoir_faire(chemin_fichier, rpps_valides):
    """
    Lit le fichier des savoir-faire (specialites).
    Filtre pour ne garder que les RPPS des prescripteurs retenus.
    """
    print(f"\n[3/3] Traitement PS_LibreAcces_SavoirFaire")
    print(f"Fichier : {chemin_fichier}")

    chunks_filtres = []
    total_brut = 0

    for chunk in pd.read_csv(
        chemin_fichier,
        sep="|",
        encoding="utf-8",
        chunksize=50_000,
        low_memory=False,
        dtype=str,
        na_values=[""],
        keep_default_na=False,
    ):
        total_brut += len(chunk)
        chunk.columns = chunk.columns.str.strip()

        if "Identifiant_PP" in chunk.columns:
            masque = chunk["Identifiant_PP"].isin(rpps_valides)
            chunk_filtre = chunk[masque].copy()
        else:
            chunk_filtre = chunk.copy()

        cols_disponibles = {
            k: v for k, v in COLONNES_SAVOIR_FAIRE.items()
            if k in chunk_filtre.columns
        }
        chunk_filtre = chunk_filtre[list(cols_disponibles.keys())].rename(
            columns=cols_disponibles
        )

        chunks_filtres.append(chunk_filtre)

    df = pd.concat(chunks_filtres, ignore_index=True)

    print(f"  Lignes brutes lues    : {total_brut:,}")
    print(f"  Lignes retenues       : {len(df):,}")
    print(f"  RPPS avec specialite  : {df['rpps'].nunique():,}")

    if "libelle_sf" in df.columns:
        print(f"\n  Top 15 specialites :")
        top = df["libelle_sf"].value_counts().head(15)
        for specialite, n in top.items():
            print(f"    {specialite} : {n:,}")

    return df


# --------------------------------------------------------------------
# ETAPE 4 — CONSTRUCTION DE LA TABLE CONSOLIDEE
# --------------------------------------------------------------------

def construire_table_prescripteurs(df_personne, df_savoir_faire):
    """
    Construit la table finale des prescripteurs autorises.

    Logique :
    - Une ligne par RPPS (pas une ligne par situation d'exercice)
    - On garde la premiere situation d'exercice active comme adresse principale
    - On joint la specialite principale depuis SavoirFaire
    - On ajoute un flag is_actif = True (tous les PS dans le fichier sont actifs)
    """
    print(f"\n[Consolidation] Construction table prescripteurs_autorises")

    # Deduplication : un RPPS peut avoir plusieurs situations d'exercice
    # On garde une ligne par RPPS en prenant le premier enregistrement
    # (le fichier est tri par RPPS et situation d'exercice)
    df_unique = df_personne.drop_duplicates(subset=["rpps"], keep="first").copy()

    # Joindre la specialite principale depuis SavoirFaire
    # Un prescripteur peut avoir plusieurs savoir-faire
    # On prend le premier (generalement la specialite principale)
    if not df_savoir_faire.empty:
        sf_principale = df_savoir_faire.drop_duplicates(
            subset=["rpps"], keep="first"
        )[["rpps", "code_sf", "libelle_sf", "code_type_sf", "libelle_type_sf"]]

        df_unique = df_unique.merge(sf_principale, on="rpps", how="left")

    # Ajouter les colonnes utiles pour la detection de fraude
    df_unique["is_actif"] = True   # Tous les PS dans le fichier sont autorises
    df_unique["date_chargement"] = pd.Timestamp.now()

    # Construire l'adresse complete
    df_unique["adresse_complete"] = (
        df_unique.get("numero_voie", pd.Series(dtype=str)).fillna("").astype(str) + " " +
        df_unique.get("libelle_type_voie", pd.Series(dtype=str)).fillna("").astype(str) + " " +
        df_unique.get("libelle_voie", pd.Series(dtype=str)).fillna("").astype(str)
    ).str.strip()

    print(f"  RPPS uniques dans la table finale : {len(df_unique):,}")

    if "code_profession" in df_unique.columns:
        print(f"\n  Repartition finale par profession :")
        for code, libelle in PROFESSIONS_PRESCRIPTEURS.items():
            n = (df_unique["code_profession"] == code).sum()
            print(f"    {libelle} : {n:,} prescripteurs")

    if "code_departement" in df_unique.columns:
        dept_rhone = df_unique["code_departement"] == "69"
        print(f"\n  Prescripteurs departement 69 (Rhone) : {dept_rhone.sum():,}")

    return df_unique


# --------------------------------------------------------------------
# ETAPE 5 — CHARGEMENT EN BASE POSTGRESQL
# --------------------------------------------------------------------

def creer_schema_et_tables(engine):
    """Cree le schema referentiels et les tables si elles n'existent pas."""

    sql = """
    -- Schema pour les referentiels externes
    CREATE SCHEMA IF NOT EXISTS referentiels;

    -- Table principale des prescripteurs autorises a prescrire un arret maladie
    CREATE TABLE IF NOT EXISTS referentiels.prescripteurs_autorises (
        rpps                    VARCHAR(11) PRIMARY KEY,
        civilite                VARCHAR(10),
        nom_exercice            VARCHAR(100),
        prenom_exercice         VARCHAR(100),
        code_profession         VARCHAR(5),
        libelle_profession      VARCHAR(100),
        code_categorie          VARCHAR(5),
        libelle_categorie       VARCHAR(100),
        code_mode_exercice      VARCHAR(5),
        libelle_mode_exercice   VARCHAR(50),
        -- Specialite principale (depuis SavoirFaire)
        code_sf                 VARCHAR(10),
        libelle_sf              VARCHAR(200),
        code_type_sf            VARCHAR(10),
        libelle_type_sf         VARCHAR(100),
        -- Adresse du cabinet / structure d'exercice principale
        numero_voie             VARCHAR(10),
        libelle_type_voie       VARCHAR(50),
        libelle_voie            VARCHAR(100),
        adresse_complete        VARCHAR(300),
        code_postal             VARCHAR(5),
        libelle_commune         VARCHAR(100),
        code_commune            VARCHAR(5),
        code_departement        VARCHAR(3),
        libelle_departement     VARCHAR(100),
        -- Structure d'exercice
        raison_sociale_site     VARCHAR(300),
        finess_site             VARCHAR(9),
        siret_site              VARCHAR(14),
        code_secteur_activite   VARCHAR(10),
        libelle_secteur_activite VARCHAR(200),
        code_genre_activite     VARCHAR(10),
        libelle_genre_activite  VARCHAR(200),
        -- Contact
        telephone               VARCHAR(20),
        -- Statut
        is_actif                BOOLEAN DEFAULT TRUE,
        date_chargement         TIMESTAMP DEFAULT NOW()
    );

    -- Index pour les jointures rapides avec SIAM
    CREATE INDEX IF NOT EXISTS idx_prescripteurs_rpps
        ON referentiels.prescripteurs_autorises(rpps);

    CREATE INDEX IF NOT EXISTS idx_prescripteurs_profession
        ON referentiels.prescripteurs_autorises(code_profession);

    CREATE INDEX IF NOT EXISTS idx_prescripteurs_departement
        ON referentiels.prescripteurs_autorises(code_departement);

    CREATE INDEX IF NOT EXISTS idx_prescripteurs_commune
        ON referentiels.prescripteurs_autorises(code_postal);

    -- Table des diplomes et autorisations d'exercice
    CREATE TABLE IF NOT EXISTS referentiels.diplomes_prescripteurs (
        id                      SERIAL PRIMARY KEY,
        rpps                    VARCHAR(11),
        code_diplome            VARCHAR(20),
        libelle_diplome         VARCHAR(300),
        code_type_diplome       VARCHAR(10),
        libelle_type_diplome    VARCHAR(100),
        numero_diplome          VARCHAR(50),
        date_obtention_diplome  VARCHAR(10),
        code_categorie_diplome  VARCHAR(10),
        libelle_categorie_diplome VARCHAR(100),
        date_chargement         TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_diplomes_rpps
        ON referentiels.diplomes_prescripteurs(rpps);

    -- Table des savoir-faire complets (toutes specialites par RPPS)
    CREATE TABLE IF NOT EXISTS referentiels.savoir_faire_prescripteurs (
        id                  SERIAL PRIMARY KEY,
        rpps                VARCHAR(11),
        code_type_sf        VARCHAR(10),
        libelle_type_sf     VARCHAR(100),
        code_sf             VARCHAR(10),
        libelle_sf          VARCHAR(200),
        date_chargement     TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_sf_rpps
        ON referentiels.savoir_faire_prescripteurs(rpps);
    """

    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    print("Schema et tables crees (ou deja existants)")


def charger_en_base(df_prescripteurs, df_diplomes, df_savoir_faire, engine):
    """Charge les trois tables en base PostgreSQL."""

    print(f"\n[Chargement PostgreSQL]")

    # Table principale
    colonnes_table = [
        "rpps", "civilite", "nom_exercice", "prenom_exercice",
        "code_profession", "libelle_profession",
        "code_categorie", "libelle_categorie",
        "code_mode_exercice", "libelle_mode_exercice",
        "code_sf", "libelle_sf", "code_type_sf", "libelle_type_sf",
        "numero_voie", "libelle_type_voie", "libelle_voie", "adresse_complete",
        "code_postal", "libelle_commune", "code_commune",
        "code_departement", "libelle_departement",
        "raison_sociale_site", "finess_site", "siret_site",
        "code_secteur_activite", "libelle_secteur_activite",
        "code_genre_activite", "libelle_genre_activite",
        "telephone", "is_actif", "date_chargement",
    ]
    cols_disponibles = [c for c in colonnes_table if c in df_prescripteurs.columns]
    df_a_charger = df_prescripteurs[cols_disponibles]

    df_a_charger.to_sql(
        name="prescripteurs_autorises",
        schema="referentiels",
        con=engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5_000
    )
    print(f"  prescripteurs_autorises : {len(df_a_charger):,} lignes chargees")

    # Table diplomes
    if not df_diplomes.empty:
        df_diplomes["date_chargement"] = pd.Timestamp.now()
        df_diplomes.to_sql(
            name="diplomes_prescripteurs",
            schema="referentiels",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=5_000
        )
        print(f"  diplomes_prescripteurs : {len(df_diplomes):,} lignes chargees")

    # Table savoir-faire complets
    if not df_savoir_faire.empty:
        df_savoir_faire["date_chargement"] = pd.Timestamp.now()
        df_savoir_faire.to_sql(
            name="savoir_faire_prescripteurs",
            schema="referentiels",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=5_000
        )
        print(f"  savoir_faire_prescripteurs : {len(df_savoir_faire):,} lignes chargees")


# --------------------------------------------------------------------
# POINT D'ENTREE
# --------------------------------------------------------------------

if __name__ == "__main__":

    import sys

    # Dossier contenant les trois fichiers telecharges
    # Adapter ce chemin selon l'emplacement reel des fichiers
    DOSSIER = Path("data/temp/rpps")

    # Detecter automatiquement les fichiers
    # Les noms incluent la date d'extraction : PS_LibreAcces_Personne_activite_20260226.txt
    def trouver_fichier(dossier, prefixe):
        fichiers = list(dossier.glob(f"{prefixe}*.txt"))
        if not fichiers:
            print(f"ERREUR : aucun fichier {prefixe}*.txt trouve dans {dossier}")
            sys.exit(1)
        # Prendre le plus recent si plusieurs
        return sorted(fichiers)[-1]

    f_personne    = trouver_fichier(DOSSIER, "PS_LibreAcces_Personne_activite")
    f_diplomes    = trouver_fichier(DOSSIER, "PS_LibreAcces_Dipl_AutExerc")
    f_savoir_faire = trouver_fichier(DOSSIER, "PS_LibreAcces_SavoirFaire")

    print("=" * 60)
    print("Traitement referentiel RPPS — Prescripteurs AAT")
    print("=" * 60)
    print(f"Fichier 1 : {f_personne.name}")
    print(f"Fichier 2 : {f_diplomes.name}")
    print(f"Fichier 3 : {f_savoir_faire.name}")

    # Etape 1 — Fichier principal
    df_personne = traiter_personne_activite(f_personne)

    # Extraire le set de RPPS valides pour filtrer les deux autres fichiers
    rpps_valides = set(df_personne["rpps"].dropna().unique())
    print(f"\n{len(rpps_valides):,} RPPS de prescripteurs identifies")

    # Etape 2 — Diplomes
    df_diplomes = traiter_diplomes(f_diplomes, rpps_valides)

    # Etape 3 — Savoir-faire
    df_sf = traiter_savoir_faire(f_savoir_faire, rpps_valides)

    # Etape 4 — Table consolidee
    df_final = construire_table_prescripteurs(df_personne, df_sf)

    # Etape 5 — Chargement PostgreSQL
    engine = get_engine()
    creer_schema_et_tables(engine)
    charger_en_base(df_final, df_diplomes, df_sf, engine)

    print("\n" + "=" * 60)
    print("Traitement termine avec succes")
    print("=" * 60)
    print(f"\nTables disponibles dans le schema referentiels :")
    print(f"  - referentiels.prescripteurs_autorises  ({len(df_final):,} prescripteurs)")
    print(f"  - referentiels.diplomes_prescripteurs   ({len(df_diplomes):,} diplomes)")
    print(f"  - referentiels.savoir_faire_prescripteurs ({len(df_sf):,} savoir-faire)")
    print(f"\nPour valider le chargement, executer dans DBeaver :")
    print("""
    SELECT code_profession, libelle_profession, COUNT(*) AS nb
    FROM referentiels.prescripteurs_autorises
    GROUP BY code_profession, libelle_profession
    ORDER BY nb DESC;
    """)
