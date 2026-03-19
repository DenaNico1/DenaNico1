# Architecture et feuille de route — Système data science fraude CPAM

## Contexte et contraintes

- Accès à SIAM ERASME en lecture seule via DBeaver (connexion Oracle)
- Espace de travail dédié sur le serveur CPAM
- Données nominatives restent dans l'espace serveur dédié
- Des requêtes SIAM régulières existent déjà — les récupérer avant de commencer
- Tuteur non technique — les livrables doivent être lisibles sans compétences data

---

## Vue d'ensemble de l'architecture

```
SIAM ERASME                Ton système                    Outputs
(Oracle — lecture          (ce que tu construis)          metier
 seule)

+----------+   Requetes   +---------------------+       +----------+
|  VAAT    | -----------> |  Zone d'extraction  |       |Dashboard |
|  VRJS    |   SQL        |  (fichiers parquet) |       |Streamlit |
|  VARR    |   DBeaver    +---------------------+       +----------+
|  VPIJ    |              |  Zone analytique    | ----> +----------+
|  VPRN    |              |  (features ML)      |       |Alertes   |
|  VBEN    |              +---------------------+       |email     |
|  VPRA    |              |  Zone modeles       |       +----------+
|  ...     |              |  (MLflow + scores)  |       +----------+
+----------+              +---------------------+       |Rapports  |
                                   |                     |controle  |
                            PostgreSQL local             +----------+
                            ou fichiers parquet
```

---

## Phase 1 — Exploration et cadrage (Semaines 1-3)

### Semaine 1 — Recuperer l'existant

La premiere chose a faire est de demander a voir les requetes SIAM existantes.
Meme si elles ne font pas exactement ce que tu veux, elles apportent deux choses :
la logique des filtres metier deja valides par l'equipe, et la certitude que
la syntaxe Oracle fonctionne dans cet environnement.

Installer DBeaver et configurer la connexion SIAM. Tester une requete simple
sur VAAT pour valider l'acces aux donnees.

### Semaines 2-3 — Exploration des donnees

Avant de construire quoi que ce soit, repondre a ces questions sur les donnees reelles.

```sql
-- Combien d'AAT sur 12 mois ?
SELECT COUNT(*) FROM VAAT
WHERE AATDTD_AAT >= ADD_MONTHS(SYSDATE, -12)
  AND GESCAT_AAT = 'TON_CODE_CPAM';

-- Combien de rejets dans VRJS ? Ce sont les labels.
SELECT RJSTYP_RJS, COUNT(*)
FROM VRJS
GROUP BY RJSTYP_RJS;

-- Distribution des durees d'arret
SELECT
    ROUND(AATDTF_AAT - AATDTD_AAT) AS duree_jours,
    COUNT(*) AS nb_arrets
FROM VAAT
WHERE AATDTD_AAT >= ADD_MONTHS(SYSDATE, -12)
GROUP BY ROUND(AATDTF_AAT - AATDTD_AAT)
ORDER BY duree_jours;
```

Ces trois requetes donnent une vision immediate du volume et de la qualite
des donnees disponibles. Les resultats constituent les premiers chiffres
a presenter au tuteur.

---

## Phase 2 — Construction de la couche d'extraction (Semaines 3-6)

### Organisation du travail avec DBeaver

DBeaver est l'outil principal pour construire et tester les requetes.
Un fichier `.sql` par theme est cree dans le dossier `requetes/` sur le serveur.
Les requetes sont testees dans DBeaver, les resultats exportes en CSV,
puis convertis en parquet par un script Python.

```
Workflow DBeaver :
1. Ouvrir requetes/arrets_maladie.sql dans DBeaver
2. Executer et verifier les resultats
3. Exporter -> Format CSV -> data/raw/arrets_maladie_202404.csv
4. Script Python lit le CSV et le convertit en parquet propre
```

### Requete 1 — Rejets et signalements VRJS (priorite absolue)

Source des labels de fraude confirmes.

```sql
-- requetes/01_labels_rejets.sql
SELECT
    r.RJSIDT_RJS,
    r.RJSCOD_RJS,
    r.RJSTYP_RJS,
    r.RSMCOD_RJS,
    r.RSMLIB_RJS,
    r.CLODTE_RJS,
    r.SRCIDT_RJS,
    a.ASSMAC_AAT,
    a.AATDTD_AAT,
    a.AATDTF_AAT,
    a.PRERPA_AAT,
    a.PREDUR_AAT
FROM VRJS r
JOIN VAAT a ON a.AATIDT_AAT = r.HSTIDT_RJS
           AND a.SRCIDT_AAT = r.SRCIDT_RJS
WHERE r.CLODTE_RJS >= ADD_MONTHS(SYSDATE, -24)
ORDER BY r.CLODTE_RJS DESC
```

### Requete 2 — Avis d'arret de travail VAAT

```sql
-- requetes/02_avis_arret_travail.sql
SELECT
    a.AATIDT_AAT,
    a.ASSMAC_AAT,
    a.GESCAT_AAT,
    a.PREDUR_AAT,
    a.AATDTD_AAT,
    a.AATDTF_AAT,
    a.PRERPA_AAT,
    a.PRENUM_AAT,
    a.ACPASS_AAT,
    a.IBODTE_AAT,
    a.NUMTOP_AAT,
    a.ADVTOP_AAT,
    a.CAETYE_AAT,
    a.CAENOM_AAT,
    a.BDICOD_AAT,
    a.SFRNBR_AAT,
    a.SRCIDT_AAT,
    sme.SMECOD_SME,
    sme.SMELIB_SME,
    rsq.RSQCOD_RSQ,
    rsq.RSQLIB_RSQ
FROM VAAT a
LEFT JOIN VSME_V sme ON sme.SMEIDT_SME = a.SMEIDT_AAT
                     AND sme.SRCIDT_SME = a.SRCIDT_AAT
LEFT JOIN VRSQ_V rsq ON rsq.RSQIDT_RSQ = a.RSQIDT_AAT
                     AND rsq.SRCIDT_RSQ = a.SRCIDT_AAT
WHERE a.GESCAT_AAT = 'TON_CODE_CPAM'
  AND a.AATDTD_AAT >= ADD_MONTHS(SYSDATE, -24)
ORDER BY a.AATDTD_AAT DESC
```

### Requete 3 — Prescripteurs VPRN + VPRA

```sql
-- requetes/03_prescripteurs_arrets.sql
SELECT
    p.ASSMAC_PRN,
    p.PRNDSD_PRN,
    p.PRNDSF_PRN,
    p.PRNNAT_PRN,
    p.PRENUM_PRN,
    p.RPSNÚM_PRN,
    p.SPÉCOD_PRN,
    p.RAPSOÎ_PRN,
    p.PASCAR_PRN,
    p.AV1COD_PRN,
    pr.PRASPE_PRA,
    pr.PRACOM_PRA,
    pr.CNVMTF_PRA,
    pr.EXCNAT_PRA
FROM VPRN p
LEFT JOIN VPRA pr ON SUBSTR(pr.PRANUM_PRA, 1, 8) = SUBSTR(p.PRENUM_PRN, 1, 8)
WHERE p.PRNDSD_PRN >= ADD_MONTHS(SYSDATE, -24)
  AND p.PRNNAT_PRN IN ('001', '002')
```

### Requete 4 — Paiements IJ VPIJ

```sql
-- requetes/04_ij_paiements.sql
SELECT
    i.DCOREF_PIJ,
    i.ASSMAC_PIJ,
    i.TPMDRI_PIJ,
    i.ASUNAT_PIJ,
    i.PRENUM_PIJ,
    i.NORPPS_PIJ,
    i.PRESPE_PIJ,
    i.PREMTT_PIJ,
    i.PERDRD_PIJ,
    i.PERDRF_PIJ,
    i.IJPNBT_PIJ,
    i.IJPMNT_PIJ,
    i.REMMNT_PIJ,
    i.EMPNUM_PIJ,
    i.MTTNUM_PIJ,
    i.CARDEL_PIJ,
    i.IJPCOD_PIJ,
    i.SANTUX_PIJ
FROM VPIJ i
WHERE i.CAIORG_PIJ = 'TON_CODE_CPAM'
  AND i.TPMDRI_PIJ >= ADD_MONTHS(SYSDATE, -24)
```

---

## Phase 3 — Construction de la couche analytique (Semaines 6-10)

### Script de conversion CSV vers Parquet

```python
# code/extraction/convert_to_parquet.py
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

def csv_vers_parquet(nom_fichier_csv, nom_fichier_parquet, description):
    """
    Lit un CSV exporte depuis DBeaver,
    nettoie et sauvegarde en parquet avec metadonnees.
    """
    chemin_csv     = Path(f"data/raw/{nom_fichier_csv}")
    chemin_parquet = Path(f"data/raw/{nom_fichier_parquet}")
    chemin_meta    = Path(f"data/raw/{nom_fichier_parquet.replace('.parquet', '_meta.json')}")

    df = pd.read_csv(chemin_csv, encoding='utf-8', sep=';', low_memory=False)

    # Dates Oracle au format YYYYMMDD -> datetime
    colonnes_dates = [c for c in df.columns if any(
        mot in c.lower() for mot in ['dsd', 'dsf', 'dsi', 'dte', 'dat', 'dtd', 'dtf']
    )]
    for col in colonnes_dates:
        try:
            df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')
        except Exception:
            pass

    # Remplacer les dates Oracle manquantes (16000101)
    for col in df.select_dtypes(include='datetime64').columns:
        df[col] = df[col].where(df[col].dt.year > 1800, other=pd.NaT)

    df.to_parquet(chemin_parquet, index=False)

    meta = {
        "description":     description,
        "source":          "SIAM ERASME V30.0.0",
        "fichier_csv":     nom_fichier_csv,
        "date_extraction": datetime.now().isoformat(),
        "nb_lignes":       len(df),
        "colonnes":        list(df.columns),
    }
    chemin_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    print(f"OK {nom_fichier_parquet} -- {len(df):,} lignes")
    return df


csv_vers_parquet("vrjs_export.csv", "labels_rejets.parquet",
                 "Rejets et signalements AAT -- labels fraude")

csv_vers_parquet("vaat_export.csv", "avis_arret_travail.parquet",
                 "Avis d'arret de travail 24 mois")

csv_vers_parquet("vprn_export.csv", "prescriptions_repos.parquet",
                 "Prescriptions de repos 24 mois")

csv_vers_parquet("vpij_export.csv", "ij_paiements.parquet",
                 "Paiements IJ 24 mois")
```

### Script de feature engineering

```python
# code/analytique/features_assures.py
import pandas as pd
import numpy as np

def construire_features():

    arrets = pd.read_parquet("data/raw/avis_arret_travail.parquet")
    prn    = pd.read_parquet("data/raw/prescriptions_repos.parquet")
    ij     = pd.read_parquet("data/raw/ij_paiements.parquet")
    labels = pd.read_parquet("data/raw/labels_rejets.parquet")

    arrets['duree_jours'] = (
        arrets['AATDTF_AAT'] - arrets['AATDTD_AAT']
    ).dt.days

    feat = arrets.groupby('ASSMAC_AAT').agg(
        nb_arrets_24m        = ('AATIDT_AAT', 'count'),
        duree_totale_jours   = ('duree_jours', 'sum'),
        duree_moyenne        = ('duree_jours', 'mean'),
        nb_prescripteurs     = ('PRERPA_AAT', 'nunique'),
        nb_arrets_zone_grise = ('duree_jours',
                                 lambda x: ((x >= 45) & (x <= 59)).sum()),
        nb_arrets_courts     = ('duree_jours',
                                 lambda x: (x < 10).sum()),
        pct_num              = ('NUMTOP_AAT', 'mean'),
        pct_adv              = ('ADVTOP_AAT', 'mean'),
    ).reset_index()

    feat['zscore_nb_arrets'] = (
        feat['nb_arrets_24m'] - feat['nb_arrets_24m'].mean()
    ) / feat['nb_arrets_24m'].std()

    sbg = ij.groupby('ASSMAC_PIJ')['EMPNUM_PIJ'].nunique().reset_index()
    sbg.columns = ['ASSMAC_AAT', 'nb_employeurs_ij']
    feat = feat.merge(sbg, on='ASSMAC_AAT', how='left')
    feat['signal_sans_employeur'] = (
        feat['nb_employeurs_ij'].isna() | (feat['nb_employeurs_ij'] == 0)
    ).astype(int)

    labels_pivot = labels.groupby('ASSMAC_AAT').agg(
        fraude_confirmee = ('RJSTYP_RJS', lambda x: (x == 'F').any().astype(int))
    ).reset_index()
    feat = feat.merge(labels_pivot, on='ASSMAC_AAT', how='left')
    feat['fraude_confirmee'] = feat['fraude_confirmee'].fillna(0).astype(int)

    feat.to_parquet("data/features/dataset_assures.parquet", index=False)

    print(f"Dataset : {len(feat):,} assures")
    print(f"Labels positifs : {feat['fraude_confirmee'].sum():,} "
          f"({feat['fraude_confirmee'].mean()*100:.2f}%)")
    return feat
```

---

## Phase 4 — Modeles et dashboard (Semaines 10-18)

A ce stade les donnees sont propres et les labels construits.
Le ML peut commencer : XGBoost, SHAP values, MLflow pour le tracking,
Streamlit pour le dashboard.

Le dashboard doit tourner sur le serveur, pas sur le poste local,
pour etre accessible au tuteur et aux controleurs sans installation.

```bash
uv run streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Structure du projet

```
stage_cpam_fraude/
|
|-- README.md                    <- Comment installer et lancer
|-- pyproject.toml               <- Dependances (gere par uv)
|-- .gitignore                   <- Exclure data/, mlruns/, .env
|-- .env                         <- Credentials SIAM (JAMAIS versionne)
|-- run_pipeline.py              <- Point d'entree unique
|
|-- extraction/
|   |-- requetes/
|   |   |-- 01_labels_rejets.sql
|   |   |-- 02_avis_arret_travail.sql
|   |   |-- 03_prescripteurs_arrets.sql
|   |   `-- 04_ij_paiements.sql
|   |-- connexion.py
|   `-- convert_to_parquet.py
|
|-- analytique/
|   |-- features_assures.py
|   |-- features_prescripteurs.py
|   `-- labels.py
|
|-- modeles/
|   |-- entrainement.py
|   |-- scoring.py
|   `-- validation.py
|
|-- dashboard/
|   `-- app.py
|
|-- data/                        <- JAMAIS dans git
|   |-- raw/
|   |-- features/
|   `-- scores/
|
|-- mlruns/                      <- MLflow local
`-- logs/
```

---

## Script d'orchestration

```python
# run_pipeline.py
from extraction.convert_to_parquet import csv_vers_parquet
from analytique.features_assures import construire_features
from modeles.scoring import scorer_assures
from datetime import datetime

if __name__ == "__main__":
    print(f"=== Pipeline fraude -- {datetime.now()} ===")

    print("\n[1/3] Conversion CSV -> Parquet")
    csv_vers_parquet("vrjs_export.csv",  "labels_rejets.parquet",       "Labels fraude")
    csv_vers_parquet("vaat_export.csv",  "avis_arret_travail.parquet",  "AAT 24 mois")
    csv_vers_parquet("vprn_export.csv",  "prescriptions_repos.parquet", "PRN 24 mois")
    csv_vers_parquet("vpij_export.csv",  "ij_paiements.parquet",        "IJ 24 mois")

    print("\n[2/3] Feature engineering")
    construire_features()

    print("\n[3/3] Scoring")
    scorer_assures()

    print("\n=== Termine ===")
```

---

## Orchestration selon le niveau de maturite

### Niveau 1 — Manuel (semaines 1-6)

Lancer `run_pipeline.py` manuellement apres chaque export DBeaver.
Simple, pas de dependances complexes, adapte a la phase de validation.

### Niveau 2 — Tache planifiee Windows (mois 3-4)

Creer une tache planifiee Windows qui lance le pipeline chaque lundi matin.
Pas besoin d'Airflow pour demarrer.

```bat
:: pipeline_hebdo.bat
cd C:\Users\ton_nom\stage_cpam
call uv run python run_pipeline.py >> logs\pipeline_%date%.log 2>&1
```

### Niveau 3 — Airflow (mois 5-6 si l'infrastructure le permet)

Donne une visibilite complete sur les executions et permet de rejouer
une etape en cas d'echec. A mettre en place uniquement une fois
que le pipeline tourne correctement en niveau 1 ou 2.

---

## Regles a respecter

**Separer extraction et analyse**
Les requetes SQL ne font qu'extraire, sans transformation.
Toute la logique metier est dans Python.
Cela permet de rejouer l'analyse sans retourner dans SIAM.

**Versionner les requetes, jamais les donnees**
Les fichiers `.sql` sont dans git.
Les fichiers `.parquet` ne le sont jamais.
Les donnees CPAM ne doivent pas sortir de l'espace serveur controle.

**Documenter la tracabilite**
Chaque dataset doit savoir d'ou il vient.
Un fichier `_meta.json` accompagne chaque parquet avec :
la requete source, la date d'extraction, le nombre de lignes,
la periode couverte et les filtres appliques.

---

## Precautions techniques SIAM

- Jointures BO AAT : toujours inclure `SRCIDT_xxx` pour eviter les doublons
- Axe Prestations (VPIJ) : filtrer sur `CAIORG_PIJ` = code de la caisse
- Axe Offre de Soins (VAIPIJ) : filtrer sur `CAIPRE_PIJ` pour les prescripteurs
- Profondeur historique : VARR/VIJP/VPRN = 24 mois, BO AAT (VAAT/VRJS) = 5 ans
- TOPBDO = 1 : donnees actives, TOPBDO = 0 : conservees 24 mois mais inactives
- Dates manquantes : valeur 01/01/1600 dans SIAM = valeur absente
- Cle de jointure prestations : DCOREF_PIJ + LIGNUM_PIJ, ne jamais joindre sur ASSMAC seul

---

## Premiere action a faire

Demander a voir une des requetes SIAM existantes avant d'ecrire quoi que ce soit.
Elle donnera le code de la caisse, la syntaxe Oracle valide dans cet environnement,
et potentiellement des filtres metier deja valides par l'equipe.
Trente minutes de conversation qui font gagner deux semaines de travail.
