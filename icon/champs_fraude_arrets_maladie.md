# 📋 Champs SIAM ERASME — Détection de fraude Arrêts Maladie

> **Source** : Dictionnaire des données SIAM ERASME V30.0.0  
> **Usage** : Construction du système d'information pour la détection de fraude aux IJ

---

## 🟦 VAAT — Avis d'Arrêt de Travail (domaine BO AAT)

> Table centrale pour la détection des faux arrêts achetés en ligne et des RPPS volés.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `AATIDT_AAT` | Identifiant technique de l'AAT | Clé primaire — jointure entre tables BO AAT |
| `ASSMAC_AAT` | Matricule de l'assuré | Identifiant de l'assuré concerné |
| `GESCAT_AAT` | Caisse gestionnaire | Filtrer sur la CPAM du Rhône |
| `PREDUR_AAT` | Durée de la prescription (nb jours) | Durée prescrite — contournement seuil 60j |
| `AATDTD_AAT` | Date de début de l'AAT | Période de l'arrêt |
| `AATDTF_AAT` | Date de fin de l'AAT | Durée réelle de l'arrêt |
| `PRENUM_AAT` | N° AM du praticien prescripteur | Identifiant prescripteur |
| `PRERPA_AAT` | N° RPPS transmis (ADELI ou RPPS) | **Signal RPPS volé** — vérifier vs référentiel VPRA |
| `ETANUM_AAT` | N° FINESS de l'établissement prescripteur | Cohérence établissement prescripteur |
| `SIRNUM_AAT` | N° SIRET de l'établissement prescripteur | Cohérence établissement |
| `RECDTE_AAT` | Date de réception de l'AAT | Délai entre prescription et réception |
| `DTEREP_AAT` | Date de reprise de travail | Cohérence avec durée prescrite |
| `SMEDTE_AAT` | Date de traitement médical | Délai traitement médical |
| `ACPASS_AAT` | Statut activité professionnelle de l'assuré | **Signal fort** — cohérence avec demande IJ |
| `BDICOD_AAT` | Code postal de l'employeur | Géolocalisation employeur |
| `VILEMP_AAT` | Ville de l'employeur | Géolocalisation employeur |
| `IBODTE_AAT` | Date d'injection dans le back-office | **Détection RPPS volé** — pic soudain d'injections |
| `ADVTOP_AAT` | Top adresse de visite différente | Adresse de contrôle différente = fuite possible |
| `NUMTOP_AAT` | Top numérisation | Faux arrêts souvent numérisés |
| `PPJTOP_AAT` | Top présence d'une pièce jointe | AAT numérisé avec pièce jointe |
| `SFRNBR_AAT` | Nb tentatives échouées d'appel au SFR | Coordonnées potentiellement falsifiées |
| `TLCTOP_AAT` | Top téléconsultation | Mode de prescription — cohérence |
| `CAETYE_AAT` | Type de canal d'entrée | **Signal réseau** — même canal pour plusieurs AAT frauduleux |
| `CAENOM_AAT` | Nom du canal d'entrée | Identification du logiciel émetteur |
| `CAEVLG_AAT` | Version du logiciel canal d'entrée | Cohérence logiciel prescripteur |
| `SRCIDT_AAT` | Identifiant de la base BO AAT source | **Obligatoire** dans toutes les jointures BO AAT |
| `TRRTOP_AAT` | Top reprise du travail | Reprise déclarée |
| `RTPTOP_AAT` | Top reprise à temps partiel | Mi-temps thérapeutique |
| `SHRTO_AAT` | Top sorties autorisées | Conditions de l'arrêt |
| `SADIDT_AAT` | ID statut traitement administratif | Jointure avec VSAD_V |
| `SMEIDT_AAT` | ID statut traitement médical | Jointure avec VSME_V |
| `RSQIDT_AAT` | ID risque de l'AAT | Jointure avec VRSQ_V (maladie / AT / MP) |
| `TATIDT_AAT` | ID type de l'AAT | Jointure avec VTAT_V |
| `NRTIDT_AAT` | ID nature de la reprise de travail | Jointure avec VNRT_V |
| `MMEIDT_AAT` | ID motif médical de l'AAT | Motif médical — cohérence diagnostic |

---

## 🟦 VRJS — Rejets et Signalements AAT (domaine BO AAT)

> **Table clé pour le labeling** : contient les AAT déjà rejetés ou signalés = labels positifs quasi-gratuits.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `RJSIDT_RJS` | ID technique du rejet | Clé primaire |
| `AATIDT_RJS` | ID technique de l'AAT (via HSTIDT) | Jointure avec VAAT |
| `RJSCOD_RJS` | Code rejet par le service médical/administratif | **Label fraude** — nature du rejet |
| `RJSTYP_RJS` | Type de rejet / signalement | Rejet médical vs administratif |
| `RSMCOD_RJS` | Code retour service métier | Motif détaillé |
| `RJCCOD_RJS` | Code complémentaire justifiant le rejet | Détail supplémentaire |
| `RSMLIB_RJS` | Libellé court retour service métier | Description lisible du rejet |
| `CLODTE_RJS` | Date de clôture de l'AAT | Date de traitement |
| `HSTIDT_RJS` | ID historique statut AAT | Jointure avec VHST |
| `SRCIDT_RJS` | ID base BO AAT source | Obligatoire pour jointures BO AAT |
| `GESCAT_RJS` | Caisse gestionnaire | Filtrage CPAM |

---

## 🟦 VHST — Historique Statut AAT (domaine BO AAT)

> Suivi des actions sur chaque dossier AAT — permet de voir l'évolution du traitement.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `HSTIDT_HST` | ID historique statuts | Clé primaire |
| `AATIDT_HST` | ID technique de l'AAT | Jointure avec VAAT |
| `SADIDT_HST` | ID statut traitement administratif | Statut courant |
| `SDOIDT_HST` | ID nature du statut du dossier | Jointure avec VSDO_V |
| `CODAGT_HST` | N° agent administratif gérant le dossier | Traçabilité agent |
| `ACTDTE_HST` | Date clôture signalement / action sur le dossier | Historique des actions |
| `ECHDTE_HST` | Date d'échéance de l'action envisagée | Suivi des délais |
| `SICTOP_HST` | Top signalement clôturé | Signalement traité |
| `SRCIDT_HST` | ID base BO AAT source | Obligatoire pour jointures |

---

## 🟩 VARR — Arrêt de Travail (domaine Bénéficiaire / BDO Famille)

> Table des arrêts de travail enregistrés — côté gestion administrative et financière.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_ARR` | Matricule de l'assuré | Identifiant assuré — jointure |
| `GESCAT_ARR` | Caisse gestionnaire | Filtrage CPAM |
| `ARRDSD_ARR` | Date de début d'arrêt | Période de l'arrêt |
| `ARRDSF_ARR` | Date de fin d'arrêt | Durée de l'arrêt |
| `ARRASU_ARR` | Nature d'assurance (V961) | Maladie ordinaire vs AT/MP vs maternité |
| `DJIDSI_ARR` | Dernier jour de travail | Cohérence avec DSN employeur |
| `GJBMON_ARR` | Gain journalier de base | Montant de référence pour calcul IJ |
| `IJBMON_ARR` | Montant de l'IJ base normale | Montant IJ théorique |
| `GJBPAY_ARR` | Montant de l'IJ de base payé | Montant IJ réellement payé |
| `TRREXI_ARR` | Code reprise du travail | Reprise déclarée |
| `RAPSOÎ_ARR` | Soins en rapport avec l'affection | Cohérence diagnostic/soins |
| `MEDNÁTI_ARR` | Nature avis médical (V401) | Type d'avis médical |
| `RGMCDF_ARR` | Régime affecté (V655) | Régime de prise en charge |
| `SINNUM_ARR` | Numéro de sinistre | Lien avec AT si applicable |
| `TOPBDO_ARR` | Top présent dans la BDO | Statut d'activité du dossier |

---

## 🟩 VIJP — Période Indemnisée Individuelle (domaine Bénéficiaire / BDO Famille)

> Détail des périodes d'indemnisation — clé pour détecter les patterns de versement.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_IJP` | Matricule de l'assuré | Identifiant assuré |
| `GESCAT_IJP` | Caisse gestionnaire | Filtrage CPAM |
| `ARRDSD_IJP` | Date de début d'arrêt | Rattachement à l'arrêt |
| `ARRASU_IJP` | Nature d'assurance (V961) | Type de risque |
| `IJPCOD_IJP` | Code nature prestations espèces (V759) | Type d'IJ — maladie / maternité / AT |
| `DESNÚM_IJP` | Numéro employeur | **Signal subrogation** — employeur associé |
| `PERDSD_IJP` | Date de début de période | Période d'indemnisation |
| `PERDSF_IJP` | Date de fin de période | Durée de la période |
| `IJPNBR_IJP` | Nombre d'IJ payées dans la période | Volume d'indemnisation |
| `IJPMON_IJP` | Montant IJ unitaire | Montant journalier |
| `IJPDNB_IJP` | Dénombrement IJ | Nombre comptabilisé |
| `SUBÉXI_IJP` | Existence subrogation | **Signal fraude** — absence anormale chez salarié |
| `SUBTOP_IJP` | Top subsistance | Cas particulier de gestion |
| `SALCOM_IJP` | Salaire comparatif | Référence salariale |
| `PRNNAT_IJP` | Nature de prescription (V461) | Type de prescription de repos |
| `PRNDSD_IJP` | Date de début PRN | Date de la prescription |
| `REVNAT_IJP` | Nature revalorisation | Revalorisation appliquée |
| `ECRTOP_IJP` | Top écrêtement | IJ plafonnée |

---

## 🟩 VPRN — Prescriptions de Repos (domaine Bénéficiaire / BDO Famille)

> Table des prescriptions médicales de repos — source principale côté médecin prescripteur.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_PRN` | Matricule de l'assuré | Identifiant assuré |
| `GESCAT_PRN` | Caisse gestionnaire | Filtrage CPAM |
| `PRNDSD_PRN` | Date début de PRN | Date de début de la prescription |
| `PRNDSF_PRN` | Date fin de PRN | Durée de la prescription |
| `PRNNAT_PRN` | Nature prescription (V461) | Type : maladie, maternité, AT... |
| `PRENUM_PRN` | Numéro prescripteur | Identifiant médecin prescripteur |
| `RPSNÚM_PRN` | Numéro RPPS | **Clé** — vérification vs VPRA.PRANUM_PRA |
| `RPSIND_PRN` | Contrôle sur la clé RPPS | Validité du RPPS |
| `SPÉCOD_PRN` | Spécialité praticien (V269) | Cohérence spécialité / diagnostic |
| `RAPSOÍ_PRN` | Soins en rapport avec affection | Présence ALD associée |
| `PASCAR_PRN` | Pas de carence | **Signal** — accumulation d'exceptions à la carence |
| `AV1COD_PRN` | Nature avis PRN1 (V401) | Avis médical 1 |
| `AV1DSD_PRN` | Date début avis PRN1 | Période avis médical |
| `AV1DSF_PRN` | Date fin avis PRN1 | Durée avis médical |
| `SA1TAU_PRN` | Taux sanction 1 | Sanction appliquée |
| `AV2COD_PRN` | Nature avis PRN2 (V401) | Avis médical 2 |
| `SA2TAU_PRN` | Taux sanction 2 | Sanction 2 |
| `SINNUM_PRN` | Numéro de sinistre | Lien AT si applicable |
| `TOPBDO_PRN` | Top présent dans la BDO | Statut actif |

---

## 🟩 VPIJ — Paiement d'Indemnités Journalières (domaine Prestations)

> Table des paiements IJ — côté comptable / remboursements effectués.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `DCOREF_PIJ` | Référence informatique du décompte | **Clé de jointure** entre toutes tables prestations |
| `LIGNUM_PIJ` | Numéro de ligne du décompte | Clé de jointure |
| `TPMDRI_PIJ` | Date de mandatement | Date effective du paiement |
| `ASSMAC_PIJ` | Matricule assuré | Identifiant assuré |
| `BENIDF_PIJ` | Identifiant du bénéficiaire | Bénéficiaire concerné |
| `ASUNAT_PIJ` | Nature assurance du décompte (V961) | Type de risque |
| `PRENUM_PIJ` | Numéro prescripteur | Identifiant médecin |
| `PRESPE_PIJ` | Spécialité du prescripteur (V269) | Cohérence spécialité |
| `PREMTT_PIJ` | Indicateur prescripteur médecin traitant | **Signal** — arrêt hors médecin traitant |
| `NORPPS_PIJ` | N° RPPS du médecin prescripteur | Validation RPPS prescripteur |
| `PRNDRD_PIJ` | Date début prescription arrêt | Date de l'arrêt |
| `CARDEL_PIJ` | Délai de carence | Carence appliquée ou non |
| `PERDRD_PIJ` | Date de début de la période d'IJ | Période d'indemnisation |
| `PERDRF_PIJ` | Date de fin de la période d'IJ | Durée indemnisée |
| `SALMJR_PIJ` | Gain journalier de base | Montant de référence |
| `IJPCOD_PIJ` | Code nature de l'IJ (V759) | Type d'IJ |
| `IJPNBT_PIJ` | Nombre d'IJ payées de la période | Volume payé |
| `IJPMNT_PIJ` | Montant de l'IJ de la période | Montant de la période |
| `IJBMNT_PIJ` | Montant IJ de base normale | IJ théorique |
| `REMMNT_PIJ` | Montant remboursé | Montant final versé |
| `SANTUX_PIJ` | Taux de la sanction | Sanction éventuelle |
| `EMPNUM_PIJ` | Numéro employeur | **Signal subrogation** — employeur associé au paiement |
| `MTTNUM_PIJ` | Numéro du Médecin Traitant | Référence médecin traitant déclaré |
| `CAIORG_PIJ` | Caisse origine | Filtrage axe prestations |
| `CAIPRE_PIJ` | Caisse gestionnaire du prescripteur | Filtrage axe offre de soins |
| `ETMNAT_PIJ` | Nature exonération TM (V988) | Exonération ALD |
| `RAPSOI_PIJ` | Soins en rapport avec l'affection | ALD associée |

---

## 🟩 VSAL — Salaires (domaine Bénéficiaire / BDO Famille)

> Données salariales de l'assuré — référence pour le calcul des IJ et détection d'incohérences.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_SAL` | Matricule de l'assuré | Identifiant assuré |
| `EMPNUM_SAL` | Numéro Employeur | Employeur déclaré |
| `SALDSI_SAL` | Date échéance salaire | Période salariale |
| `SALBAS_SAL` | Montant salaire Brut AS | Salaire de référence |
| `SALNAS_SAL` | Montant salaire Net AS | Salaire net |
| `TRANBJ_SAL` | Nombre de jours travaillés | Jours déclarés travaillés |
| `SALMIT_SAL` | Top Salaire mi-temps | Mi-temps thérapeutique |
| `CATPRO_SAL` | Catégorie Socio-Professionnelle | Contexte socio-professionnel |
| `INDSMI_SAL` | Indicateur de SMIC | Niveau de rémunération |
| `TOPBDO_SAL` | Top présent dans la BDO | Statut actif |

---

## 🟩 VSBG — Subrogation (domaine Bénéficiaire / BDO Famille)

> Table des subrogations — **signal clé** pour détecter les fraudeurs sans employeur réel.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_SBG` | Matricule de l'assuré | Identifiant assuré |
| `SBGNUM_SBG` | Numéro employeur subrogé | Employeur qui avance les IJ |
| `SBGDSD_SBG` | Date de début subrogation | Période de subrogation |
| `SBGDSF_SBG` | Date de fin subrogation | Fin de la subrogation |
| `TOPBDO_SBG` | Top présent dans la BDO | **Clé signal** — absence de ligne = pas de subrogation |

---

## 🟧 VBEN — Bénéficiaires (domaine Bénéficiaire / BDO Famille)

> Référentiel des assurés — données socio-démographiques pour contextualiser les analyses.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_BEN` | Matricule de l'assuré | Identifiant assuré |
| `BENIDF_BEN` | Identifiant du bénéficiaire | Clé bénéficiaire |
| `GESCAT_BEN` | Caisse gestionnaire | Filtrage CPAM |
| `NAÍANN_BEN` | Année de naissance | Calcul de l'âge — analyse toutes tranches |
| `NAIMÓI_BEN` | Mois de naissance | Précision date naissance |
| `NAIJOU_BEN` | Jour de naissance | Précision date naissance |
| `BENSEX_BEN` | Sexe du bénéficiaire | Contextualisation profil |
| `BENQLT_BEN` | Qualité du bénéficiaire (V501) | Assuré / ayant-droit / retraité |
| `AGECLS_BEN` | Classe d'âge | Tranche d'âge — **signal** car fraude touche tous les âges |
| `DCDDSR_BEN` | Date de décès du bénéficiaire | **Règle métier** — arrêt après décès = alerte immédiate |
| `ET1NAT_BEN` | Nature exonération TM 1ère occ. (V451) | ALD active — contextualisation |
| `ET1DSD_BEN` | Date début exonération 1ère occ. | Période ALD |
| `ET1DSF_BEN` | Date fin exonération 1ère occ. | Fin ALD |
| `RSDDPT_BEN` | Département de résidence | Géolocalisation assuré |
| `RSDCCM_BEN` | Commune de résidence | Géolocalisation précise |
| `TOPBDO_BEN` | Top présent dans la BDO | Statut actif |

---

## 🟧 VADR — Adresses des Bénéficiaires (domaine Bénéficiaire / BDO Famille)

> Adresses détaillées — utiles pour détecter les incohérences géographiques.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_ADR` | Matricule de l'assuré | Identifiant assuré |
| `BENIDF_ADR` | Identifiant du bénéficiaire | Clé bénéficiaire |
| `ADRDSD_ADR` | Date début d'effet adresse | Période de validité adresse |
| `ADÉDSF_ADR` | Date fin d'effet adresse | Fin de validité adresse |
| `BDICOD_ADR` | Code postal | Localisation assuré |
| `RSDLIB_ADR` | Libellé commune de résidence | Commune de résidence |
| `RSDCCM_ADR` | Code commune de résidence | Code INSEE commune |
| `RSDDPT_ADR` | Code département de résidence | Département |
| `ACTIVE_ADR` | Adresse active lors du dernier chargement | Adresse courante |
| `NPACOD_ADR` | Code NPAI | N'habite pas à l'adresse indiquée |

---

## 🟧 VMTT — Médecin Traitant (domaine Bénéficiaire / BDO Famille)

> Déclaration du médecin traitant — référence pour détecter les arrêts prescrits hors MT.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_MTT` | Matricule de l'assuré | Identifiant assuré |
| `BENIDF_MTT` | Identifiant du bénéficiaire | Clé bénéficiaire |
| `PRANUM_MTT` | Numéro de praticien du médecin traitant | **Référence MT** — comparer avec PRENUM des arrêts |
| `DCLDSD_MTT` | Date de début du contrat MT | Période de déclaration MT |
| `DCLDÉF_MTT` | Date de fin du contrat MT | Fin de déclaration MT |
| `MTFCOD_MTT` | Code motif de résiliation | Raison changement MT |

---

## 🟥 VPRA — Praticiens (domaine Praticiens / FNPS)

> Référentiel des professionnels de santé — **validation des RPPS** et profils prescripteurs.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `PRANUM_PRA` | Numéro du praticien | **Clé** — validation existence praticien |
| `PRACAI_PRA` | Caisse gestionnaire du praticien | CPAM gestionnaire du médecin |
| `PRASPE_PRA` | Spécialité du praticien (V269) | Cohérence spécialité / actes prescrits |
| `PRACOM_PRA` | Code commune du cabinet | Géolocalisation cabinet |
| `PRABDI_COD` | Code postal du cabinet | Code postal cabinet |
| `PRADPT_PRA` | Département d'exercice | Département du médecin |
| `CNVMTF_PRA` | Situation conventionnelle (V274) | Médecin conventionné ou non |
| `CNVDSD_PRA` | Date d'effet situation conventionnelle | Période convention |
| `EXCNAT_PRA` | Code nature de l'exercice (V283) | Nature d'exercice (libéral, salarié...) |
| `EXCMTF_PRA` | Code motif de fin d'exercice (V284) | Médecin en fin d'activité |
| `ACPDRD_PRA` | Date début d'activité libérale | Médecin récemment installé |
| `PRACAT_PRA` | Code catégorie du praticien (V270) | Type de professionnel |
| `AGEDLS_PRA` | Classe d'âge du praticien | Âge du prescripteur |
| `SIRNÚM_PRA` | Numéro de SIRET | Identification fiscale |
| `FINNUM_PRA` | Numéro de FINESS géographique | Établissement de rattachement |
| `DOSDTM_PRA` | Date de dernière mise à jour | Fraîcheur de l'information |

---

## 🟥 VDRA — Justificatif Ouverture de Droits PE (domaine Bénéficiaire / BDO Famille)

> Justificatifs d'ouverture de droits prestations en espèces — conditions d'éligibilité.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_DRA` | Matricule de l'assuré | Identifiant assuré |
| `DRTNAT_DRA` | Nature JOD PE | Type de justificatif |
| `EMPNUM_DRA` | Numéro Employeur | Employeur au moment de l'ouverture |
| `DRTDSD_DRA` | Date début d'effet ouverture de droits | Période d'éligibilité |
| `DRTDSF_DRA` | Date fin d'effet ouverture de droits | Fin d'éligibilité |
| `DRTNBH_DRA` | Nombre d'heures salariés | Heures travaillées déclarées |
| `DRTRÉM_DRA` | Rémunération | Rémunération déclarée |

---

## 🟥 VAMF — Contexte Médico-Administratif (domaine Bénéficiaire / BDO Famille)

> Contexte médico-administratif global du dossier — suivi des interventions.

| Champ | Description | Usage fraude |
|-------|-------------|--------------|
| `ASSMAC_AMF` | Matricule de l'assuré | Identifiant assuré |
| `CMANAT_AMF` | Nature du Contexte Médico-Administratif (V401) | Type d'intervention |
| `CMADSD_AMF` | Date de début du CMA | Début du contexte |
| `CMADSF_AMF` | Date de fin du CMA | Fin du contexte |
| `RETNBR_AMF` | Nombre de réceptions tardives | Anomalies de réception |
| `PITDSI_AMF` | Dates du PIT (1ère interruption de travail) | Première interruption — historique |

---

## 🔲 Tables de référence BO AAT (vues de valeurs)

> Tables de valeurs pour décoder les codes des vues BO AAT.

| Table | Champ clé | Description |
|-------|-----------|-------------|
| `VSDO_V` | `SDOCOD_SDO`, `SDOLIB_SDO` | Libellés statuts du dossier AAT |
| `VSAD_V` | `SADCOD_SAD`, `SADLIB_SAD` | Libellés statuts traitement administratif |
| `VSME_V` | `SMECOD_SME`, `SMELIB_SME` | Libellés statuts traitement médical |
| `VRSQ_V` | `RSQCOD_RSQ`, `RSQLIB_RSQ` | Libellés risques (maladie / AT / MP) |
| `VTAT_V` | `TTACOD_TAT`, `TTALIB_TAT` | Libellés types d'AAT |
| `VNRT_V` | `NRTCOD_NRT`, `NRTLIB_NRT` | Libellés natures de reprise de travail |

---

## 📌 Récapitulatif par table

| Table | Domaine | Nb champs retenus | Rôle principal |
|-------|---------|-------------------|----------------|
| `VAAT` | BO AAT | 35 | Document AAT — faux arrêts / RPPS volés |
| `VRJS` | BO AAT | 11 | **Labels fraude** — rejets et signalements |
| `VHST` | BO AAT | 9 | Historique traitement dossier |
| `VARR` | Bénéficiaire | 16 | Arrêt administratif — durée, montants |
| `VIJP` | Bénéficiaire | 18 | Périodes d'indemnisation — subrogation |
| `VPRN` | Bénéficiaire | 19 | Prescriptions de repos — RPPS, carence |
| `VPIJ` | Prestations | 27 | Paiements IJ effectués |
| `VSAL` | Bénéficiaire | 10 | Salaires déclarés |
| `VSBG` | Bénéficiaire | 5 | Subrogation — signal clé fraude |
| `VBEN` | Bénéficiaire | 15 | Profil assuré — âge, ALD, décès |
| `VADR` | Bénéficiaire | 10 | Adresses — cohérence géographique |
| `VMTT` | Bénéficiaire | 6 | Médecin traitant déclaré |
| `VPRA` | Praticiens | 17 | Référentiel prescripteurs — validation RPPS |
| `VDRA` | Bénéficiaire | 7 | Justificatifs ouverture droits |
| `VAMF` | Bénéficiaire | 6 | Contexte médico-administratif |
| `VSDO_V / VSAD_V / VSME_V / VRSQ_V / VTAT_V / VNRT_V` | BO AAT | — | Tables de valeurs / libellés |

---

## ⚠️ Précautions techniques importantes

- **Jointures BO AAT** : toujours inclure `SRCIDT_xxx` pour éviter les doublons (données multi-instances)
- **Axe Prestations** (`VPIJ`) : filtrer sur `CAIORG_PIJ` = votre caisse pour voir les assurés affiliés
- **Axe Offre de Soins** (`VAIPIJ`) : filtrer sur `CAIPRE_PIJ` pour voir les prescripteurs gérés par votre caisse
- **Profondeur historique** : VARR/VIJP/VPRN = 24 mois — BO AAT (VAAT/VRJS) = **5 ans**
- **TOPBDO = 1** : données actives dans la BDO — **TOPBDO = 0** : conservées 24 mois mais inactives
- **Dates manquantes** : valeur `01/01/1600` dans SIAM = valeur absente — toujours filtrer
- **ASSMAC** : anonymisé (ANO) dans certains contextes — utiliser `BENIDF` pour les jointures bénéficiaires
- **Clé jointure prestations** : `DCOREF_PIJ + LIGNUM_PIJ` — ne jamais joindre sur `ASSMAC` seul dans le domaine prestations
