# Rapport — Dossier `scripts` : Construction de données et analyse

https://github.com/arj7192/fight_fraud_with_machine_learning

## Contexte général

Ce dossier contient un **pipeline complet de détection de fraude à priori sur les Prescriptions de Repos Nécessitant (PRN / arrêts de travail IJ)** pour la CNAM (CPAM 91 — Essonne, région Île-de-France). L'objectif est de scorer des PRN avant leur traitement afin de prioriser les contrôles agents, en utilisant un modèle de machine learning.

Le pipeline est organisé en **9 scripts numérotés** (0 à 8), mêlant notebooks Jupyter et requêtes SQL.

---

## Architecture des données

### Sources d'entrée

| Source | Format | Contenu |
|---|---|---|
| **BO AAT** | Excel `impressionResultatsRecherche-JJMMAAAA.xls` | Extractions des PRN papier (NIR, dates, prescripteur, durée, nature, type) |
| **ERASME** | Oracle SQL (via SQL Developer) | Informations bénéficiaire : âge, sexe, régime, C2S, ALD, historique consultations |
| **Retours contrôle agents** | Excel (arborescence année/mois) | Résultats des contrôles : colonne `PRN FRAUDULEUSE OUI/NON` |

---

## Description script par script

### `0_packages_check.ipynb` — Vérification environnement

Vérifie la présence de tous les packages Python requis (`numpy`, `pandas`, `sklearn`, `plotly`, `nbformat`, etc.). Indique si l'installation est complète ou si des packages manquent.

---

### `1_creation_base.ipynb` + `1_creation_base_controle_prio_ij_v5.sql` — Création de la base d'entraînement initiale

**Construction de données — point de départ.**

- **Entrée** : fichier Excel `ctr_prn_demarrage.xlsx` avec des PRN déjà contrôlées manuellement (NIR, dates début/fin, durée, nature, type, prescripteur, label FRAUDE OUI/NON).
- **Nettoyage** : standardisation du label FRAUDE, typage des NIR et prescripteurs.
- **Requête SQL ERASME** : à partir des NIR + date début PRN, la requête croise 5 vues Oracle (`vben_bdo`, `vmtt_bdo`, `vfam_bdo`, `vmll`, `vact`) pour récupérer :
  - Age bénéficiaire (calculé depuis DDN)
  - Sexe
  - Médecin Traitant (MTT)
  - Régime PR806 (régime particulier)
  - Statut C2S (Complémentaire Santé Solidaire) à la date de la PRN
  - Statut ALD (Affection Longue Durée)
  - Présence d'une consultation chez le prescripteur dans les 7 jours précédant la PRN
- **Feature engineering** :
  - `PRESC_MTT` : le prescripteur est-il le médecin traitant du bénéficiaire ? (OUI/NON)
  - `DUREE` : durée calculée (date fin - date début + 1)
  - `DEPOT_TARDIF` : dépôt après la date de fin ? (OUI/NON)
  - `DELAI_DEPOT` : nombre de jours entre début PRN et dépôt
  - `DELAI_DEPOT_TARDIF` : nombre de jours de retard
  - `CAT_PS` : catégorie du prescripteur (3e chiffre du N° AM)
  - `TX_FRAUDE` : taux de fraude historique par prescripteur (calculé sur la base entière)
- **Filtres qualité** : retrait des durées aberrantes (< 0 ou ≥ 365 jours), retrait des âges < 1 an.
- **Sortie** : CSV versionné `ctr_prn_91_YYYYMMDD.csv` + Excel `liste_ps_prn.xlsx` (taux de fraude par PS).

---

### `2_preparation_entrainement.ipynb` — Préparation des données pour l'entraînement

**Transformation des données brutes en matrice modèle.**

- **Filtres** : durée < 365j, retrait ALD (`ETM == "non"`), filtrage sur nature TC uniquement, dédoublonnage.
- **Discrétisation de la durée** (`DUREE_CLASSE`) : 4 classes (inf30, 30_60, 60_100, 100plus).
- **One-hot encoding** des variables catégorielles : TYPE, PR806, DEPOT_TARDIF, C2S, PRESC_MTT, SEXE, DUREE_CLASSE, CONSULT, FRAUDE.
- **Classes d'âge** : 22 classes (0-1, 1-5, 5-10, ..., 95-100, 100+), encodées en binaire avec préfixe `CLASSE_AGE_`.
- **CPAM prescripteur** : extraction des 2 premiers chiffres du N° AM, one-hot par département + indicateurs booléens `PRESC_91` (propre CPAM) et `PRESC_REGION` (Île-de-France).
- **CAT_PS** : one-hot sur catégorie prescripteur.
- **Variables continues conservées** : DUREE, TX_FRAUDE, DELAI_DEPOT, DELAI_DEPOT_TARDIF.
- **Nettoyage final** : suppression des colonnes `_NON` redondantes et des colonnes à variance nulle (valeur unique).
- **Sortie** : `train_data_clean.csv`.

---

### `3_entrainement.ipynb` — Entraînement du modèle

**Modélisation machine learning.**

- **Split train/test 50/50** avec stratification optimisée automatiquement (algorithme itératif qui maximise les colonnes utilisées pour stratifier tout en garantissant un minimum d'exemples par strate — priorité sur FRAUDE_OUI, C2S, DUREE_CLASSE, SEXE).
- **Suréchantillonnage** (`resample`) :
  - Sur-représentation des cas non-C2S (diagnostic d'erreur en production).
  - Rééquilibrage positifs/négatifs (fraude minoritaire).
- **Recherche par grille (GridSearchCV, KFold 5 plis)**, scoring F1 weighted, avec MinMaxScaler en pipeline. Modèles candidats : Random Forest, AdaBoost, XGBoost, Logistic Regression, KNN, Linear SVC, Gradient Boosting, Decision Tree, Dummy classifiers.
- **Sélection du meilleur modèle** avec détection over/underfitting (marge 0.1 entre F1 train et F1 test).
- **Analyse post-hoc** :
  - Recherche du seuil de positivité optimal (0.1 à 0.9, maximisation F1).
  - Analyse des performances par sous-catégorie de chaque variable binaire.
  - Visualisation importance des variables (coefficients ou feature importances).
- **Versionning** : log des modèles dans `model_log.xlsx` (date, données source, nom modèle).
- **Sortie** : modèle sérialisé `.pkl`, `model_cols.csv` (liste des colonnes du modèle).

---

### `4_preparation_traitement.ipynb` + `4_controle_prio_ij_v5.sql` — Préparation du traitement en production

**Collecte et préparation des nouvelles PRN à scorer.**

- Scanne le répertoire `extractions/` pour les fichiers BO AAT (`impressionResultatsRecherche-*.xls`).
- Consolidation de tous les fichiers en un seul DataFrame, nettoyage des NIR, conversion des dates au format ERASME (AAAAMMJJ).
- Sauvegarde `NIR.csv` pour la requête ERASME + pickle de la liste des fichiers à traiter.
- La requête SQL `4_controle_prio_ij_v5.sql` est identique à la version entraînement mais inclut en plus le **nom patronymique** du bénéficiaire et les **codes régime actifs** (RGMCOD1/2/3 si date fin > aujourd'hui), utiles pour les contrôleurs. Sortie : `info_ben_ij_prio.csv`.

---

### `5_traitement.ipynb` — Traitement en production (scoring)

**Application du modèle sur les nouvelles PRN.**

- Chargement et consolidation des exports DEMAT AAT + résultats ERASME (historique glissant).
- Jointure DEMAT AAT ↔ ERASME par hash (NIR + date début + prescripteur).
- Reconstruction de toutes les features (identiques à l'entraînement) : durée, dépôt tardif, délais, PRESC_MTT, age, CAT_PS, taux fraude PS.
- **Alignement sur les colonnes du modèle** (`model_cols.csv`) : ajout des colonnes manquantes à 0 pour garantir la compatibilité.
- Chargement du modèle `.pkl` et **prédiction** (`predict` + `predict_proba`).
- Application optionnelle d'un seuil de positivité personnalisé (`SEUIL_POSITIF`).
- Filtres de production : exclusion de certains profils (ALD, ETM).
- Possibilité de filtrer par durée minimale (`DUREE`) et délai de dépôt (`DELAI`).
- **Génération des fichiers de diffusion** par date, organisés en arborescence `diffusions/ANNEE/MOIS/`.
- **Archivage** des extractions AAT traitées.
- **Mise à jour du fichier récapitulatif** `recap_ctrl_prn.xlsx` (fichier source, modèle utilisé, volumes, nombre de prédictions positives).

---

### `6_monitoring.ipynb` — Suivi des performances en production

**Analyse des résultats suite contrôle agents.**

- Lecture de tous les fichiers de retour contrôle (arborescence `controles/ANNEE/MOIS/`).
- Calcul du **F1 score par fichier** (comparaison `FRAUDES` prédit vs `CONTROLE` réel).
- Calcul de la **moyenne mobile sur 5 traitements** (F1 rolling).
- Jointure avec `recap_ctrl_prn.xlsx` pour associer chaque fichier au modèle utilisé.
- **Analyses graphiques (Plotly)** :
  - Structure des contrôles (répartition % par type, nature, sexe, CPAM, PR806, C2S, classe durée, PRESC_MTT, fraude).
  - Structure de la fraude détectée par contrôle agents.
  - **Analyse des erreurs** : structure des cas mal prédits.
  - Évolution du F1 score par date et par modèle (courbes + moyenne mobile).
  - F1 moyen par version de modèle.
- **Sorties** : `monitoring_recap.xlsx`, `resultats_controles.xlsx`.

---

### `7_maj_base.ipynb` — Mise à jour de la base d'entraînement

**Alimentation continue de la base avec les retours contrôle.**

- Consolidation de tous les fichiers de retour contrôle agents.
- Nettoyage et standardisation des labels FRAUDE.
- **Détection des nouvelles observations** par hash (NIR + début PRN + prescripteur) — évite les doublons.
- Jointure avec l'historique ERASME (fichier `histo_info_ben_ij_prio.csv`) pour récupérer les informations complémentaires déjà calculées en production (évite de re-interroger ERASME).
- Feature engineering identique à `1_creation_base.ipynb`.
- **Gestion de la fenêtre de rétention ERASME** : conservation uniquement des 12 derniers mois dans l'historique (purge automatique).
- Recalcul du taux de fraude par prescripteur sur la base mise à jour.
- **Sortie** : nouveau CSV versionné `ctr_prn_91_YYYYMMDD.csv`.

---

### `8_convertisseur_notebook.ipynb` — Utilitaire de conversion

Convertit un notebook `.ipynb` en script `.py` via `nbconvert`. Permet de déployer les notebooks sous forme de scripts Python autonomes.

---

## Résumé des variables du modèle final

| Type | Variables |
|---|---|
| **Continues** | DUREE, TX_FRAUDE, DELAI_DEPOT, DELAI_DEPOT_TARDIF |
| **Binaires** | DEPOT_TARDIF_OUI, C2S_OUI, PR806_OUI, PRESC_MTT_OUI, CONSULT_OUI, SEXE_*, TYPE_* |
| **Classes durée** | DUREE_CLASSE_inf30/30_60/60_100/100plus |
| **Classes âge** | CLASSE_AGE_00 à CLASSE_AGE_CT (22 bins) |
| **CPAM prescripteur** | CPAM_75 à CPAM_95, PRESC_91_OUI, PRESC_REGION_OUI |
| **Catégorie PS** | CAT_PS_0 à CAT_PS_9 |
| **Cible** | FRAUDE_OUI (binaire) |

---

## Flux global du pipeline

```
Données contrôlées (Excel) ──► 1_creation_base ──► 2_preparation_entrainement ──► 3_entrainement
                                                                                         │
                                                                                    Modèle .pkl
                                                                                         │
Nouvelles PRN (BO AAT) ──► 4_preparation_traitement ──► SQL ERASME ──► 5_traitement ──► Fichiers diffusion
                                                                              │
                                                                    Retours contrôle agents
                                                                              │
                                                              6_monitoring ◄──┤
                                                                              │
                                                              7_maj_base ◄───┘
                                                                    │
                                                              Base enrichie ──► 2_preparation ──► 3_entrainement (ré-entraînement)
```

Le pipeline est **auto-alimenté** : les retours des contrôleurs enrichissent la base d'entraînement, permettant le ré-entraînement périodique du modèle.
