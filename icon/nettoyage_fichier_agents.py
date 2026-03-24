# nettoyage_fichier_agents.py
#
# Ce script nettoie le fichier Excel partagé par l'agent de contrôle.
# Deux transformations principales :
#   1. Séparer la colonne NIR en deux colonnes : NIR et CLE_NIR
#   2. Séparer les périodes "Du XX/XX/XXXX au XX/XX/XXXX" en deux colonnes

import pandas as pd
import re
from pathlib import Path


# --------------------------------------------------------------------
# 1. CHARGEMENT DU FICHIER
# --------------------------------------------------------------------

chemin_fichier = Path("data/temp/cas_agents_fraude.xlsx")

# Adapter sheet_name selon le nom de l'onglet dans le fichier
# D'après les images les onglets s'appellent : Expérimentation1, REUNION,
# Et. Paris, Dr GUILHEM NOUREDDINE, En Attente
df = pd.read_excel(chemin_fichier, sheet_name="Expérimentation1", header=2)

print(f"Dimensions : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print(f"Colonnes : {df.columns.tolist()}")


# --------------------------------------------------------------------
# 2. SEPARATION DU NIR ET DE LA CLE
# --------------------------------------------------------------------
# Format dans le fichier : "1 95 10 69 382 326 | 42"
# On veut :  NIR = "1 95 10 69 382 326"   CLE_NIR = "42"

def separer_nir(valeur):
    """
    Sépare une valeur de type "1 95 10 69 382 326 | 42"
    en deux parties : le NIR et la clé.
    Retourne (NIR, CLE) ou (valeur originale, None) si le format ne correspond pas.
    """
    if pd.isna(valeur):
        return None, None

    valeur_str = str(valeur).strip()

    if "|" in valeur_str:
        parties = valeur_str.split("|")
        nir = parties[0].strip()
        cle = parties[1].strip()
        return nir, cle

    # Pas de séparateur | -> on retourne la valeur brute et None pour la clé
    return valeur_str, None


# Identifier la colonne NIR
# D'après les images c'est la colonne D — adapter le nom si nécessaire
colonne_nir = "NIR"   # <- adapter si le nom de colonne est différent

if colonne_nir in df.columns:
    df[["NIR_PROPRE", "CLE_NIR"]] = df[colonne_nir].apply(
        lambda x: pd.Series(separer_nir(x))
    )
    print(f"\nSéparation NIR effectuée.")
    print(df[["NIR_PROPRE", "CLE_NIR"]].head(10))
else:
    print(f"\nATTENTION : colonne '{colonne_nir}' non trouvée.")
    print(f"Colonnes disponibles : {df.columns.tolist()}")


# --------------------------------------------------------------------
# 3. SEPARATION DES PERIODES DE DATES
# --------------------------------------------------------------------
# Format dans le fichier : "Du 01/01/2025 au 31/03/2025"
# On veut :  DATE_DEBUT = "01/01/2025"    DATE_FIN = "31/03/2025"
#
# Attention : certaines cellules contiennent plusieurs périodes
# sur plusieurs lignes, par exemple :
#   "Du 01/01/2025 au 31/03/2025
#    Du 01/05/2025 au 30/06/2025"
# Dans ce cas on extrait uniquement la première période.
# Si tu veux toutes les périodes, voir la fonction separer_toutes_periodes()

PATTERN_DATE = r"Du\s+(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})"

def separer_periode(valeur):
    """
    Extrait la première période d'une cellule.
    Retourne (DATE_DEBUT, DATE_FIN) en format datetime ou (None, None).
    """
    if pd.isna(valeur):
        return None, None

    valeur_str = str(valeur).strip()
    match = re.search(PATTERN_DATE, valeur_str, re.IGNORECASE)

    if match:
        date_debut = pd.to_datetime(match.group(1), format="%d/%m/%Y", errors="coerce")
        date_fin   = pd.to_datetime(match.group(2), format="%d/%m/%Y", errors="coerce")
        return date_debut, date_fin

    return None, None


def separer_toutes_periodes(valeur):
    """
    Extrait TOUTES les périodes d'une cellule qui en contient plusieurs.
    Retourne une liste de tuples (DATE_DEBUT, DATE_FIN).
    """
    if pd.isna(valeur):
        return []

    valeur_str = str(valeur).strip()
    matches = re.findall(PATTERN_DATE, valeur_str, re.IGNORECASE)

    periodes = []
    for debut_str, fin_str in matches:
        debut = pd.to_datetime(debut_str, format="%d/%m/%Y", errors="coerce")
        fin   = pd.to_datetime(fin_str,   format="%d/%m/%Y", errors="coerce")
        periodes.append((debut, fin))

    return periodes


# Identifier la colonne des périodes
# D'après les images c'est la dernière colonne visible (colonne K)
# Elle contient les périodes d'arrêt de travail
colonne_periodes = "Soins et/ou délivrances pendant l'arrêt de trava"
# <- adapter le nom exact de la colonne

# Si tu ne connais pas le nom exact, cherche la colonne qui contient "Du"
colonnes_avec_dates = [
    col for col in df.columns
    if df[col].astype(str).str.contains(r"Du\s+\d{2}/\d{2}/\d{4}", regex=True).any()
]
print(f"\nColonnes contenant des périodes de dates : {colonnes_avec_dates}")

# Appliquer la séparation sur chaque colonne détectée
for col in colonnes_avec_dates:
    nom_debut = f"{col}_DATE_DEBUT"
    nom_fin   = f"{col}_DATE_FIN"

    df[[nom_debut, nom_fin]] = df[col].apply(
        lambda x: pd.Series(separer_periode(x))
    )

    print(f"\nSéparation dates effectuée pour : {col}")
    print(df[[col, nom_debut, nom_fin]].dropna(subset=[nom_debut]).head(10))


# --------------------------------------------------------------------
# 4. NETTOYAGES SUPPLEMENTAIRES OBSERVES DANS LES IMAGES
# --------------------------------------------------------------------

# Colonne SCORING (colonne A dans image 2) -> convertir en numérique
if "SCORING" in df.columns or df.columns[0] == "SCORING":
    col_scoring = df.columns[0]
    df[col_scoring] = pd.to_numeric(df[col_scoring], errors="coerce")

# Colonne qui contient FAUX (colonne I dans image 1 / colonne H dans image 2)
# C'est le label fraude confirmée -> convertir en booléen
colonnes_faux = [
    col for col in df.columns
    if df[col].astype(str).str.upper().isin(["FAUX", "VRAI", "TRUE", "FALSE"]).any()
]
for col in colonnes_faux:
    df[f"{col}_BOOL"] = df[col].astype(str).str.upper().map({
        "VRAI": True,
        "TRUE": True,
        "FAUX": False,
        "FALSE": False,
    })
    print(f"\nConversion booléenne effectuée pour : {col}")
    print(df[col].value_counts())


# --------------------------------------------------------------------
# 5. SAUVEGARDE
# --------------------------------------------------------------------

# Version Excel nettoyée
chemin_sortie_excel = Path("data/temp/cas_agents_fraude_nettoye.xlsx")
df.to_excel(chemin_sortie_excel, index=False)
print(f"\nFichier Excel nettoyé sauvegardé : {chemin_sortie_excel}")

# Version CSV pour import dans PostgreSQL
chemin_sortie_csv = Path("data/temp/cas_agents_fraude_nettoye.csv")
df.to_csv(chemin_sortie_csv, index=False, sep=";", encoding="utf-8-sig")
print(f"Fichier CSV sauvegardé : {chemin_sortie_csv}")

# Résumé final
print(f"\n{'='*50}")
print(f"Résumé du fichier nettoyé")
print(f"{'='*50}")
print(f"Nombre de lignes         : {len(df):,}")
print(f"Nombre de colonnes       : {len(df.columns)}")
if "NIR_PROPRE" in df.columns:
    print(f"NIR renseignés           : {df['NIR_PROPRE'].notna().sum():,}")
    print(f"Clés NIR renseignées     : {df['CLE_NIR'].notna().sum():,}")
for col in colonnes_avec_dates:
    nom_debut = f"{col}_DATE_DEBUT"
    if nom_debut in df.columns:
        print(f"Dates début renseignées ({col[:20]}) : {df[nom_debut].notna().sum():,}")
