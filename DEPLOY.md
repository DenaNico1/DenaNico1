# 🚀 Déploiement Portfolio — denanico1.github.io

Guide complet pour mettre ton portfolio en ligne en ~10 minutes.

---

## Étape 1 — Créer le repository GitHub

1. Va sur **https://github.com/new**
2. Nom du repository : **exactement** `DenaNico1.github.io`
   > ⚠️ Le nom doit correspondre à ton username GitHub. Casse comprise.
3. Visibilité : **Public** (obligatoire pour GitHub Pages gratuit)
4. Ne coche rien (pas de README, pas de .gitignore)
5. Clique **Create repository**

---

## Étape 2 — Préparer les fichiers en local

Ouvre un terminal et exécute :

```bash
# Crée un dossier pour ton portfolio
mkdir portfolio-nico
cd portfolio-nico

# Initialise git
git init
git branch -M main

# Place ton fichier portfolio ici et renomme-le
cp /chemin/vers/portfolio-nico-final.html index.html

# Place aussi ton CV PDF ici
cp /chemin/vers/cv-nico-dena.pdf cv-nico-dena.pdf
```

Structure finale du dossier :
```
portfolio-nico/
├── index.html          ← ton portfolio (renommé)
├── cv-nico-dena.pdf    ← ton CV
└── README.md           ← optionnel
```

---

## Étape 3 — Pousser vers GitHub

```bash
# Connecte au remote GitHub
git remote add origin https://github.com/DenaNico1/DenaNico1.github.io.git

# Ajoute tous les fichiers
git add .
git commit -m "feat: initial portfolio deployment"

# Pousse
git push -u origin main
```

---

## Étape 4 — Activer GitHub Pages

1. Va sur `https://github.com/DenaNico1/DenaNico1.github.io`
2. Clique sur **Settings** (onglet en haut)
3. Dans le menu gauche : **Pages**
4. Source : **Deploy from a branch**
5. Branch : **main** / dossier : **/ (root)**
6. Clique **Save**

⏳ Attends 1-3 minutes, puis va sur :
**https://denanico1.github.io**

---

## Étape 5 — Ajouter le lien CV téléchargeable

Dans ton `index.html`, remplace les liens contact par :

```html
<!-- Dans la section contact, ajoute ce lien : -->
<a href="./cv-nico-dena.pdf" download class="cl">
  <span>↓</span> Télécharger mon CV (PDF)
</a>
```

---

## Étape 6 — Personnalisation finale avant push

Ouvre `index.html` et remplace ces placeholders :

| Chercher | Remplacer par |
|----------|---------------|
| `nico.dena@email.com` | Ton vrai email |
| `linkedin.com/in/nicodena` | Ton vrai profil LinkedIn |
| `github.com/nicodena` | `github.com/DenaNico1` |
| `nicodena1.github.io` | `denanico1.github.io` |

---

## Étape 7 — Domaine personnalisé (optionnel)

Si tu veux **nicodena.fr** ou **nico-dena.dev** :

1. Achète le domaine sur OVH (~7€/an) ou Namecheap
2. Dans GitHub Pages Settings → Custom domain → Entre ton domaine
3. Chez ton registrar, ajoute ces DNS records :
   ```
   A     @    185.199.108.153
   A     @    185.199.109.153
   A     @    185.199.110.153
   A     @    185.199.111.153
   CNAME www  denanico1.github.io
   ```
4. Coche **Enforce HTTPS** dans GitHub Pages

---

## Mises à jour futures

```bash
# Pour mettre à jour le portfolio après modifications
cd portfolio-nico
git add .
git commit -m "update: ajout projet X"
git push

# GitHub redéploie automatiquement en ~1 minute
```

---

## Checklist avant de partager le lien

- [ ] Portfolio accessible sur https://denanico1.github.io
- [ ] CV PDF téléchargeable
- [ ] Email réel dans la section contact
- [ ] Lien LinkedIn correct
- [ ] Lien GitHub correct (github.com/DenaNico1)
- [ ] Testé sur mobile
- [ ] Titre de l'onglet correct ("Nico Dena — Data Scientist...")
- [ ] Ajouter le lien sur ton profil LinkedIn (section "Site web")
- [ ] Ajouter le lien dans la signature de tes emails

---

## URL finale

```
https://denanico1.github.io
```

Partage cette URL sur :
- **LinkedIn** → Infos → Site web
- **GitHub** → Profil → Website  
- **Email** → Signature automatique
- **CV PDF** → Lien cliquable
