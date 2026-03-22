# Base de données PostgreSQL — Système de détection de fraude CPAM

---

## Pourquoi PostgreSQL plutôt que des fichiers parquet

Les fichiers parquet sont adaptés à l'exploration et au prototypage.
Pour un système qui tourne en production chaque semaine, une base de données
est indispensable pour quatre raisons concrètes.

**Concurrence** : si deux scripts tournent en même temps et écrivent dans
le même fichier parquet, les données sont corrompues. PostgreSQL gère les
transactions automatiquement.

**Requêtes analytiques** : savoir combien d'alertes ont été générées la
semaine dernière et combien ont été confirmées par les agents est une requête
SQL de 30 secondes. Avec des fichiers c'est un script Python complet.

**Mises à jour partielles** : quand un agent confirme ou infirme une alerte,
un simple UPDATE suffit. Avec un fichier parquet il faut réécrire l'intégralité.

**Maintenabilité** : dans six mois, une base avec un schéma clair est
infiniment plus facile à reprendre qu'un dossier avec quarante fichiers parquet.

---

## Choix technique

PostgreSQL est retenu pour les raisons suivantes :
- Open source, pas de coût de licence
- Robuste et mature, standard dans les projets data science professionnels
- Installation possible sur le serveur CPAM existant
- Connexion native avec SQLAlchemy et pandas
- Gestion fine des droits d'accès par schema et par utilisateur

SQLite est écarté car c'est une base fichier sans gestion des accès concurrents,
adaptée aux tests locaux uniquement.
MySQL est écarté car PostgreSQL gère mieux les types complexes et les requêtes
analytiques.
Les bases cloud sont écartées car les données nominatives doivent rester
sur le serveur CPAM.

---

## Architecture de la base de données

La base est organisée en quatre schémas distincts qui correspondent
aux quatre couches du pipeline.

```sql
CREATE SCHEMA raw;        -- Données brutes extraites de SIAM
CREATE SCHEMA features;   -- Features ML calculées
CREATE SCHEMA modeles;    -- Scores et résultats des modèles
CREATE SCHEMA metier;     -- Données métier (labels agents, alertes)
```

---

## Schéma raw — données extraites de SIAM

Ces tables reçoivent directement les exports DBeaver.
Elles sont réinitialisées à chaque extraction hebdomadaire.

```sql
-- Table principale des AAT
CREATE TABLE raw.avis_arret_travail (
    aatidt_aat          BIGINT,
    assmac_aat          VARCHAR(13),
    gescat_aat          VARCHAR(3),
    predur_aat          INTEGER,
    aatdtd_aat          DATE,
    aatdtf_aat          DATE,
    prerpa_aat          VARCHAR(11),
    prenum_aat          VARCHAR(8),
    acpass_aat          VARCHAR(2),
    ibodte_aat          DATE,
    numtop_aat          INTEGER,
    advtop_aat          INTEGER,
    caetye_aat          VARCHAR(15),
    caenom_aat          VARCHAR(80),
    bdicod_aat          VARCHAR(5),
    sfrnbr_aat          INTEGER,
    srcidt_aat          VARCHAR(5),
    date_extraction     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (aatidt_aat, srcidt_aat)
);

-- Table des rejets et signalements (labels SIAM)
CREATE TABLE raw.rejets_signalements (
    rjsidt_rjs          BIGINT PRIMARY KEY,
    aatidt_rjs          BIGINT,
    rjscod_rjs          VARCHAR(10),
    rjstyp_rjs          VARCHAR(1),
    rsmcod_rjs          VARCHAR(2),
    rsmlib_rjs          VARCHAR(70),
    clodte_rjs          DATE,
    srcidt_rjs          VARCHAR(5),
    gescat_rjs          VARCHAR(3),
    date_extraction     TIMESTAMP DEFAULT NOW()
);

-- Table des prescriptions de repos
CREATE TABLE raw.prescriptions_repos (
    assmac_prn          VARCHAR(13),
    prndsd_prn          DATE,
    prndsf_prn          DATE,
    prnnat_prn          VARCHAR(3),
    rpsnúm_prn          VARCHAR(11),
    spécod_prn          INTEGER,
    pascar_prn          VARCHAR(1),
    gescat_prn          VARCHAR(3),
    date_extraction     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (assmac_prn, prndsd_prn, prnnat_prn)
);

-- Table des paiements IJ
CREATE TABLE raw.paiements_ij (
    dcoref_pij          VARCHAR(19),
    lignum_pij          INTEGER,
    assmac_pij          VARCHAR(13),
    tpmdri_pij          DATE,
    norpps_pij          BIGINT,
    perdrd_pij          DATE,
    perdrf_pij          DATE,
    ijpnbt_pij          INTEGER,
    ijpmnt_pij          NUMERIC(9,2),
    remmnt_pij          NUMERIC(9,2),
    empnum_pij          BIGINT,
    cardel_pij          VARCHAR(2),
    date_extraction     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (dcoref_pij, lignum_pij)
);

-- Table des arrêts de travail
CREATE TABLE raw.arrets_travail (
    assmac_arr          VARCHAR(13),
    gescat_arr          VARCHAR(3),
    arrdsd_arr          DATE,
    arrdsf_arr          DATE,
    arrasu_arr          VARCHAR(2),
    djidsi_arr          DATE,
    gjbmon_arr          NUMERIC(9,2),
    ijbmon_arr          NUMERIC(9,2),
    gjbpay_arr          NUMERIC(9,2),
    trrexi_arr          VARCHAR(1),
    rgmcdf_arr          VARCHAR(3),
    date_extraction     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (assmac_arr, arrdsd_arr, arrasu_arr)
);

-- Table des bénéficiaires
CREATE TABLE raw.beneficiaires (
    assmac_ben          VARCHAR(13) PRIMARY KEY,
    benidf_ben          VARCHAR(7),
    gescat_ben          VARCHAR(3),
    naiann_ben          INTEGER,
    naimoi_ben          INTEGER,
    bensex_ben          INTEGER,
    benqlt_ben          VARCHAR(2),
    agecls_ben          VARCHAR(2),
    dcddsr_ben          DATE,
    et1nat_ben          VARCHAR(4),
    et1dsd_ben          DATE,
    et1dsf_ben          DATE,
    rsddpt_ben          VARCHAR(2),
    rsdccm_ben          VARCHAR(3),
    date_extraction     TIMESTAMP DEFAULT NOW()
);

-- Table des praticiens
CREATE TABLE raw.praticiens (
    pranum_pra          VARCHAR(8) PRIMARY KEY,
    praspe_pra          INTEGER,
    pracom_pra          VARCHAR(3),
    pradpt_pra          VARCHAR(2),
    cnvmtf_pra          VARCHAR(1),
    excnat_pra          INTEGER,
    pracat_pra          INTEGER,
    acpdrd_pra          DATE,
    finnum_pra          VARCHAR(9),
    dosdtm_pra          INTEGER,
    date_extraction     TIMESTAMP DEFAULT NOW()
);

-- Table de subrogation
CREATE TABLE raw.subrogations (
    assmac_sbg          VARCHAR(13),
    sbgnum_sbg          VARCHAR(14),
    sbgdsd_sbg          DATE,
    sbgdsf_sbg          DATE,
    topbdo_sbg          INTEGER,
    date_extraction     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (assmac_sbg, sbgnum_sbg, sbgdsd_sbg)
);
```

---

## Schéma features — datasets ML calculés

Ces tables sont recalculées à chaque run du pipeline.
Elles remplacent les fichiers parquet de features.

```sql
-- Features agrégées par assuré
CREATE TABLE features.assures (
    assmac                  VARCHAR(13) PRIMARY KEY,
    nb_arrets_24m           INTEGER,
    duree_totale_jours      INTEGER,
    duree_moyenne           NUMERIC(6,1),
    nb_prescripteurs        INTEGER,
    nb_arrets_zone_grise    INTEGER,        -- durée entre 45 et 59 jours
    nb_arrets_courts        INTEGER,        -- durée inférieure à 10 jours
    pct_num                 NUMERIC(4,3),   -- proportion AAT numérisés
    pct_adv                 NUMERIC(4,3),   -- proportion adresse visite diff.
    zscore_nb_arrets        NUMERIC(6,3),
    signal_sans_employeur   SMALLINT,       -- 1 si absence anormale subrogation
    age_assure              INTEGER,
    sexe                    VARCHAR(1),
    departement             VARCHAR(2),
    ald_active              SMALLINT,       -- 1 si ALD en cours
    date_calcul             TIMESTAMP DEFAULT NOW()
);

-- Features agrégées par prescripteur
CREATE TABLE features.prescripteurs (
    rpps                        VARCHAR(11) PRIMARY KEY,
    nb_arrets_total             INTEGER,
    nb_patients_distincts       INTEGER,
    arrets_par_patient          NUMERIC(6,2),
    pct_arrets_vendredi         NUMERIC(4,3),
    pct_arrets_lundi            NUMERIC(4,3),
    zscore_activite_semaine     NUMERIC(6,3),
    zscore_vs_specialite        NUMERIC(6,3),
    taux_rpps_injections_pic    NUMERIC(4,3),
    nb_canaux_distincts         INTEGER,
    pct_patients_distants       NUMERIC(4,3),
    specialite                  VARCHAR(3),
    commune                     VARCHAR(3),
    departement                 VARCHAR(2),
    statut_convention           VARCHAR(1),
    date_calcul                 TIMESTAMP DEFAULT NOW()
);
```

---

## Schéma metier — données des agents et alertes

Ces tables ne se réinitialisent jamais. Elles s'enrichissent au fil du temps
et constituent la mémoire institutionnelle du système.

```sql
-- Cas confirmés par les agents de contrôle
-- Alimentée par import du fichier Excel des agents
-- et enrichie progressivement
CREATE TABLE metier.cas_confirmes (
    id                  SERIAL PRIMARY KEY,
    assmac              VARCHAR(13),
    rpps_prescripteur   VARCHAR(11),
    date_arret          DATE,
    date_confirmation   DATE,
    type_fraude         VARCHAR(50),    -- faux_arret, rpps_vole, subrogation, etc.
    fraude_confirmee    BOOLEAN,
    montant_fraude      NUMERIC(10,2),
    montant_recouvre    NUMERIC(10,2),
    source              VARCHAR(50),    -- excel_controleurs, vrjs, signalement
    agent_id            VARCHAR(10),
    commentaire         TEXT,
    date_import         TIMESTAMP DEFAULT NOW()
);

-- Alertes générées par les modèles
-- Alimentée à chaque run du pipeline
-- Mise à jour par les agents quand ils traitent le dossier
CREATE TABLE metier.alertes (
    id                      SERIAL PRIMARY KEY,
    assmac                  VARCHAR(13),
    rpps_prescripteur       VARCHAR(11),
    pipeline                VARCHAR(20),    -- recouvrement ou prevention
    score_fraude            NUMERIC(5,4),
    niveau_alerte           VARCHAR(10),    -- faible, moyen, eleve
    top_features            JSONB,          -- top features SHAP en JSON
    date_generation         TIMESTAMP DEFAULT NOW(),
    run_id                  INTEGER REFERENCES modeles.runs(id),
    -- Retour agent
    statut                  VARCHAR(20) DEFAULT 'en_attente',
    -- en_attente, en_cours, confirme, infirme, hors_scope
    agent_id                VARCHAR(10),
    date_traitement         TIMESTAMP,
    fraude_confirmee        BOOLEAN,
    montant_concerne        NUMERIC(10,2),
    commentaire             TEXT
);

-- Index pour les requêtes fréquentes du dashboard
CREATE INDEX idx_alertes_statut     ON metier.alertes(statut);
CREATE INDEX idx_alertes_pipeline   ON metier.alertes(pipeline);
CREATE INDEX idx_alertes_date       ON metier.alertes(date_generation);
CREATE INDEX idx_alertes_score      ON metier.alertes(score_fraude DESC);
```

---

## Schéma modeles — tracking des runs

```sql
-- Historique des runs de modèles
CREATE TABLE modeles.runs (
    id                      SERIAL PRIMARY KEY,
    pipeline                VARCHAR(20),        -- recouvrement ou prevention
    version_modele          VARCHAR(20),
    date_run                TIMESTAMP DEFAULT NOW(),
    nb_assures_scores       INTEGER,
    nb_alertes_generees     INTEGER,
    pr_auc                  NUMERIC(5,4),
    recall                  NUMERIC(5,4),
    precision_score         NUMERIC(5,4),
    seuil_alerte            NUMERIC(5,4),
    mlflow_run_id           VARCHAR(50),
    commentaire             TEXT
);

-- Scores individuels par run
-- Permet de suivre l'évolution du score d'un assuré dans le temps
CREATE TABLE modeles.scores (
    id              SERIAL PRIMARY KEY,
    run_id          INTEGER REFERENCES modeles.runs(id),
    assmac          VARCHAR(13),
    score_fraude    NUMERIC(5,4),
    date_score      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scores_assmac  ON modeles.scores(assmac);
CREATE INDEX idx_scores_run_id  ON modeles.scores(run_id);
```

---

## Connexion Python vers PostgreSQL

### Fichier .env — credentials (jamais versionné)

```
PG_HOST=nom_serveur_cpam
PG_PORT=5432
PG_DATABASE=fraude_cpam
PG_USER=ton_login
PG_PASSWORD=ton_mdp
```

### Module de connexion

```python
# code/database/connexion.py
from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


def get_engine():
    """
    Retourne un engine SQLAlchemy connecté à PostgreSQL.
    Les credentials sont lus depuis le fichier .env.
    """
    url = (
        f"postgresql://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url, echo=False)


def lire_table(schema, table, where=None):
    """
    Lit une table depuis PostgreSQL vers un DataFrame pandas.
    Le paramètre where permet de filtrer sans charger toute la table.

    Exemple : lire_table("metier", "alertes", "statut = 'en_attente'")
    """
    engine = get_engine()
    requete = f"SELECT * FROM {schema}.{table}"
    if where:
        requete += f" WHERE {where}"
    return pd.read_sql(requete, engine)


def lire_sql(requete):
    """Exécute une requête SQL arbitraire et retourne un DataFrame."""
    engine = get_engine()
    return pd.read_sql(requete, engine)


def ecrire_table(df, schema, table, if_exists="replace"):
    """
    Ecrit un DataFrame pandas dans une table PostgreSQL.

    if_exists :
        replace -> réinitialise la table (pour raw et features)
        append  -> ajoute les lignes (pour metier et modeles)
    """
    engine = get_engine()
    df.to_sql(
        name=table,
        schema=schema,
        con=engine,
        if_exists=if_exists,
        index=False,
        method="multi",     -- insertion par batch, beaucoup plus rapide
        chunksize=10000
    )
    print(f"OK {len(df):,} lignes écrites dans {schema}.{table}")


def executer_sql(requete):
    """Exécute une requête SQL sans retour de données (UPDATE, DELETE...)."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(requete))
        conn.commit()
```

---

## Intégration dans le pipeline

```python
# run_pipeline.py
from extraction.convert_to_dataframe import csv_vers_dataframe
from database.connexion import ecrire_table, lire_table
from analytique.features_assures import construire_features_assures
from analytique.features_prescripteurs import construire_features_prescripteurs
from modeles.scoring import scorer_assures, generer_alertes
from datetime import datetime

if __name__ == "__main__":
    print(f"=== Pipeline fraude -- {datetime.now()} ===")

    # Etape 1 — Chargement des exports DBeaver en base
    print("\n[1/4] Chargement exports SIAM -> PostgreSQL (schema raw)")
    ecrire_table(csv_vers_dataframe("vaat_export.csv"),
                 "raw", "avis_arret_travail",  if_exists="replace")
    ecrire_table(csv_vers_dataframe("vrjs_export.csv"),
                 "raw", "rejets_signalements",  if_exists="replace")
    ecrire_table(csv_vers_dataframe("vprn_export.csv"),
                 "raw", "prescriptions_repos",  if_exists="replace")
    ecrire_table(csv_vers_dataframe("vpij_export.csv"),
                 "raw", "paiements_ij",         if_exists="replace")

    # Etape 2 — Feature engineering
    print("\n[2/4] Feature engineering -> PostgreSQL (schema features)")
    ecrire_table(construire_features_assures(),
                 "features", "assures",       if_exists="replace")
    ecrire_table(construire_features_prescripteurs(),
                 "features", "prescripteurs", if_exists="replace")

    # Etape 3 — Scoring
    print("\n[3/4] Scoring -> PostgreSQL (schema modeles)")
    scores = scorer_assures()
    ecrire_table(scores, "modeles", "scores", if_exists="append")

    # Etape 4 — Génération des alertes
    print("\n[4/4] Generation alertes -> PostgreSQL (schema metier)")
    alertes = generer_alertes(scores, seuil=0.7)
    ecrire_table(alertes, "metier", "alertes", if_exists="append")

    print(f"\n=== Termine -- {datetime.now()} ===")
```

---

## Structure du projet avec PostgreSQL

```
stage_cpam_fraude/
|
|-- code/
|   |-- database/
|   |   |-- connexion.py          <- Engine SQLAlchemy + fonctions utilitaires
|   |   |-- schema.sql            <- DDL complet de création des tables
|   |   `-- migrations/           <- Evolutions du schéma dans le temps
|   |       `-- 001_initial.sql
|   |
|   |-- extraction/
|   |   |-- requetes/             <- Fichiers .sql SIAM (DBeaver)
|   |   `-- convert_to_dataframe.py  <- CSV -> DataFrame (sans passer par fichier)
|   |
|   |-- analytique/
|   |   |-- features_assures.py
|   |   `-- features_prescripteurs.py
|   |
|   |-- modeles/
|   |   |-- entrainement.py
|   |   |-- scoring.py
|   |   `-- validation.py
|   |
|   `-- dashboard/
|       `-- app.py                <- Lit directement depuis PostgreSQL
|
|-- data/
|   `-- temp/                     <- CSV temporaires DBeaver
|                                    Supprimés après chargement en base
|                                    Ne jamais versionner ce dossier
|
|-- mlruns/                       <- MLflow local
|-- logs/                         <- Logs d'exécution du pipeline
|-- .env                          <- Credentials PostgreSQL (jamais versionné)
|-- .gitignore
|-- pyproject.toml
`-- run_pipeline.py
```

---

## Lecture depuis le dashboard Streamlit

Le dashboard lit directement depuis PostgreSQL sans passer par des fichiers.

```python
# dashboard/app.py (extrait)
import streamlit as st
from database.connexion import lire_sql

# Alertes en attente de traitement
alertes = lire_sql("""
    SELECT
        a.assmac,
        a.score_fraude,
        a.niveau_alerte,
        a.date_generation,
        a.statut,
        f.nb_arrets_24m,
        f.nb_prescripteurs,
        f.nb_arrets_zone_grise
    FROM metier.alertes a
    LEFT JOIN features.assures f ON f.assmac = a.assmac
    WHERE a.statut = 'en_attente'
      AND a.pipeline = 'recouvrement'
    ORDER BY a.score_fraude DESC
    LIMIT 50
""")

# Mise à jour du statut quand un agent traite un dossier
def confirmer_alerte(alerte_id, fraude_confirmee, agent_id, commentaire):
    from database.connexion import executer_sql
    executer_sql(f"""
        UPDATE metier.alertes
        SET statut           = '{"confirme" if fraude_confirmee else "infirme"}',
            fraude_confirmee = {fraude_confirmee},
            agent_id         = '{agent_id}',
            date_traitement  = NOW(),
            commentaire      = '{commentaire}'
        WHERE id = {alerte_id}
    """)
```

---

## Quand basculer de parquet vers PostgreSQL

```
Maintenant (en attente des accès SIAM)
-> Travailler en parquet sur les données Kaggle pour pratiquer
-> Installer PostgreSQL sur le serveur CPAM
-> Créer les schémas et les tables avec schema.sql

Mois 1 (premières extractions SIAM)
-> Charger directement en PostgreSQL via ecrire_table()
-> Garder parquet uniquement pour les exports temporaires DBeaver

Mois 2-3 (modèle recouvrement)
-> Tout passe par PostgreSQL
-> Parquet abandonné en production

Mois 4-6 (industrialisation)
-> PostgreSQL est la source unique de vérité
-> Le dashboard Streamlit lit directement depuis PostgreSQL
-> Les agents mettent à jour les alertes via le dashboard
```

---

## Question à poser à l'équipe informatique CPAM

Avant d'installer quoi que ce soit sur le serveur :

"Est-ce que je peux installer PostgreSQL sur l'espace serveur qui m'a été
alloué, ou est-ce qu'il faut passer par une procédure particulière pour
installer un nouveau service ?"

Dans certaines CPAM l'installation de services sur les serveurs nécessite
une validation de la DSI. Il vaut mieux le savoir en amont.

---

## Précautions importantes

**Sécurité des credentials**
Le fichier .env ne doit jamais être versionné dans git.
Vérifier que .env est bien dans le .gitignore avant le premier commit.

**Données nominatives**
Les tables du schéma raw contiennent des données nominatives (ASSMAC).
L'accès à la base PostgreSQL doit être restreint aux seuls utilisateurs
autorisés par la politique de sécurité de la CPAM.

**Sauvegardes**
Mettre en place une sauvegarde automatique de la base, notamment du schéma
metier qui contient les labels des agents — ces données ne peuvent pas être
recréées automatiquement en cas de perte.

**Nettoyage des fichiers temporaires**
Les CSV dans data/temp/ doivent être supprimés après chargement en base.
Ne jamais les laisser trainer sur le serveur.
