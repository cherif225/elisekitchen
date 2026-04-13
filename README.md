# 🍴 ELISE KITCHEN — Application Complète v3.0
## Site de Commande Client + Dashboard Administration

Application Flask prête à déployer — SQLite intégré, zéro serveur de base de données requis.

---

## ✅ Validation (100% tests réussis)

Toutes les routes public et admin sont testées et fonctionnelles :
accueil, catalogue, panier AJAX, commande complète, suivi,
dashboard admin, gestion commandes, inventaire, clients, fournisseurs, factures.

---

## 🚀 Démarrage local

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

| Interface | URL |
|-----------|-----|
| Site client | http://localhost:5000/ |
| Administration | http://localhost:5000/admin |

## 🔑 Identifiants

| Login   | Mot de passe | Rôle  |
|---------|--------------|-------|
| admin   | admin123     | Admin |
| gerant  | gerant123    | Gérant|
| caisse  | caisse123    | Caisse|

---

## 🌐 Déploiement Production

### Railway / Render (recommandé)
- Start command : `gunicorn wsgi:app`
- Variable d'env : `SECRET_KEY=votre-cle-secrete`

### VPS avec Nginx + Gunicorn
```bash
gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 2
```

### PythonAnywhere
- Upload les fichiers, pointer le WSGI vers wsgi.py

---

## 📂 Structure

```
elisekitchen/
├── app.py              ← Application Flask (35 routes)
├── init_db.py          ← Schéma SQLite + données démo
├── wsgi.py             ← Point d'entrée WSGI
├── Procfile            ← Pour Railway/Heroku
├── requirements.txt
├── instance/chegest.db ← Base SQLite (auto-créée)
├── static/css/         ← public.css + admin.css
├── static/js/          ← public.js + admin.js
└── templates/
    ├── public/         ← 10 pages client
    └── admin/          ← 14 pages dashboard
```

---

## 🌟 Fonctionnalités

### Site Client
- Accueil avec hero animé, catégories, produits vedettes
- Catalogue filtrable par catégorie + recherche
- Fiche produit avec suggestions
- Panier persistant, mise à jour AJAX
- Commande (retrait / livraison)
- Confirmation avec numéro unique
- Suivi de commande avec timeline statut

### Dashboard Admin
- Connexion sécurisée (mots de passe hashés)
- Dashboard : KPIs + graphiques Chart.js
- Commandes avec filtres par statut + changement en 1 clic
- Alertes stock faible automatiques
- Inventaire : CRUD complet
- Clients : fiche avec historique et stats
- Fournisseurs : CRUD complet
- Factures imprimables
- Polling 30s : notification nouvelle commande

© 2026 ELISE KITCHEN
