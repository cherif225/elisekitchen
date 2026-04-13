"""
ELISE KITCHEN — Application de Gestion Commerciale & Site de Commande
Version 3.0 Production — SQLite intégré, zéro dépendance externe
"""
import sqlite3
import os
import random
import string
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'elise-kitchen-prod-key-2026-xK9mPqRtYzWs')
app.config['DATABASE'] = os.environ.get(
    'DATABASE_PATH',
    os.path.join(os.path.dirname(__file__), 'instance', 'chegest.db')
)
# Durée session : 8 heures
app.config['PERMANENT_SESSION_LIFETIME'] = 28800

os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# BASE DE DONNÉES (SQLite)
# ═══════════════════════════════════════════════════════════════
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def qry(sql, args=(), one=False):
    """SELECT → retourne un dict ou une liste de dicts."""
    cur = get_db().execute(sql, args)
    rows = [dict(r) for r in cur.fetchall()]
    return rows[0] if one and rows else (None if one else rows)

def exe(sql, args=()):
    """INSERT / UPDATE / DELETE → retourne lastrowid."""
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def gen_numero():
    s = ''.join(random.choices(string.digits, k=4))
    return f"CMD-{datetime.now().strftime('%Y%m%d')}-{s}"

def login_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if 'admin_id' not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for('admin_login'))
        return f(*a, **kw)
    return deco

# ─── Filtres Jinja2 ──────────────────────────────────────────
@app.template_filter('datefr')
def datefr(v, fmt='%d/%m/%Y'):
    if not v:
        return '—'
    try:
        dt = datetime.fromisoformat(str(v)[:19])
        return dt.strftime(fmt)
    except Exception:
        return str(v)

@app.template_filter('datefr_hm')
def datefr_hm(v):
    return datefr(v, '%d/%m/%Y à %H:%M')

@app.template_filter('fcfa')
def fcfa(v):
    try:
        return f"{float(v):,.0f}".replace(',', ' ')
    except Exception:
        return '0'

@app.template_filter('statut_label')
def statut_label(s):
    return {
        'nouvelle': 'Nouvelle', 'confirmée': 'Confirmée',
        'en_preparation': 'En préparation', 'prête': 'Prête !',
        'livrée': 'Livrée', 'annulée': 'Annulée'
    }.get(s, s)

@app.template_filter('statut_css')
def statut_css(s):
    return s.replace(' ', '_').replace('é', 'e').replace('è', 'e')

# ─── Context processor ───────────────────────────────────────
@app.context_processor
def inject_globals():
    ctx = {'nouvelles_commandes': 0, 'annee': datetime.now().year}
    if 'admin_id' in session:
        try:
            row = qry("SELECT COUNT(*) as n FROM commandes WHERE statut='nouvelle'", one=True)
            ctx['nouvelles_commandes'] = row['n'] if row else 0
        except Exception:
            pass
    return ctx

# ═══════════════════════════════════════════════════════════════
# SITE PUBLIC
# ═══════════════════════════════════════════════════════════════

def _nb_panier():
    p = session.get('panier', {})
    return sum(v['quantite'] for v in p.values())

@app.route('/')
def home():
    vedettes = qry("SELECT * FROM produits WHERE en_vedette=1 AND disponible=1 ORDER BY nom LIMIT 6")
    categories = qry("""
        SELECT categorie, COUNT(*) as nb, MIN(prix) as prix_min
        FROM produits WHERE disponible=1
        GROUP BY categorie ORDER BY categorie
    """)
    return render_template('public/home.html',
        vedettes=vedettes, categories=categories, nb_panier=_nb_panier())

@app.route('/catalogue')
@app.route('/catalogue/<categorie>')
def catalogue(categorie=None):
    q = request.args.get('q', '').strip()
    sql = "SELECT * FROM produits WHERE disponible=1"
    args = []
    if categorie:
        sql += " AND categorie=?"; args.append(categorie)
    if q:
        sql += " AND (nom LIKE ? OR description_courte LIKE ?)"; args += [f'%{q}%', f'%{q}%']
    sql += " ORDER BY en_vedette DESC, nom ASC"
    produits = qry(sql, args)
    categories = qry("SELECT categorie, COUNT(*) as nb FROM produits WHERE disponible=1 GROUP BY categorie ORDER BY categorie")
    return render_template('public/catalogue.html',
        produits=produits, categories=categories,
        categorie_active=categorie, q=q, nb_panier=_nb_panier())

@app.route('/produit/<int:id>')
def produit_detail(id):
    p = qry("SELECT * FROM produits WHERE id=? AND disponible=1", (id,), one=True)
    if not p:
        abort(404)
    suggestions = qry("""
        SELECT * FROM produits WHERE categorie=? AND id!=? AND disponible=1
        ORDER BY en_vedette DESC LIMIT 4
    """, (p['categorie'], id))
    return render_template('public/produit.html',
        produit=p, suggestions=suggestions, nb_panier=_nb_panier())

# ─── PANIER ──────────────────────────────────────────────────
@app.route('/panier')
def panier():
    p = session.get('panier', {})
    items = list(p.values())
    total = sum(i['prix'] * i['quantite'] for i in items)
    return render_template('public/panier.html',
        items=items, total=total, nb_panier=_nb_panier())

@app.route('/panier/ajouter', methods=['POST'])
def ajouter_panier():
    data = request.get_json() or request.form
    pid = str(data.get('produit_id', ''))
    qty = max(1, int(data.get('quantite', 1)))
    p = qry("SELECT * FROM produits WHERE id=? AND disponible=1", (pid,), one=True)
    if not p:
        return jsonify({'success': False, 'message': 'Produit indisponible'}), 404
    panier = session.get('panier', {})
    if pid in panier:
        panier[pid]['quantite'] += qty
    else:
        panier[pid] = {'id': p['id'], 'nom': p['nom'], 'prix': float(p['prix']),
                       'emoji': p['emoji'] or '🍽️', 'categorie': p['categorie'], 'quantite': qty}
    session['panier'] = panier
    session.modified = True
    nb = sum(v['quantite'] for v in panier.values())
    return jsonify({'success': True, 'nb_panier': nb, 'message': f"« {p['nom']} » ajouté au panier !"})

@app.route('/panier/modifier', methods=['POST'])
def modifier_panier():
    data = request.get_json() or request.form
    pid = str(data.get('produit_id', ''))
    qty = int(data.get('quantite', 0))
    panier = session.get('panier', {})
    if qty <= 0:
        panier.pop(pid, None)
    elif pid in panier:
        panier[pid]['quantite'] = qty
    session['panier'] = panier
    session.modified = True
    total = sum(v['prix'] * v['quantite'] for v in panier.values())
    nb = sum(v['quantite'] for v in panier.values())
    item_total = float(panier[pid]['prix'] * panier[pid]['quantite']) if pid in panier else 0
    return jsonify({'success': True, 'total': total, 'nb_panier': nb, 'item_total': item_total})

@app.route('/panier/vider')
def vider_panier():
    session.pop('panier', None)
    return redirect(url_for('panier'))

# ─── COMMANDE ────────────────────────────────────────────────
@app.route('/commander', methods=['GET', 'POST'])
def commander():
    panier_data = session.get('panier', {})
    if not panier_data:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for('catalogue'))
    items = list(panier_data.values())
    total = sum(i['prix'] * i['quantite'] for i in items)

    if request.method == 'POST':
        nom       = request.form.get('nom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        email     = request.form.get('email', '').strip()
        adresse   = request.form.get('adresse', '').strip()
        livraison = request.form.get('type_livraison', 'retrait')
        notes     = request.form.get('notes', '').strip()

        if not nom or not telephone:
            flash("Nom et téléphone obligatoires.", "danger")
            return render_template('public/commander.html',
                items=items, total=total, nb_panier=_nb_panier())
        try:
            numero = gen_numero()
            # Client existant ou création
            client = qry("SELECT id FROM clients WHERE telephone=?", (telephone,), one=True)
            if client:
                client_id = client['id']
                exe("UPDATE clients SET nb_commandes=nb_commandes+1, total_depense=total_depense+? WHERE id=?",
                    (total, client_id))
            else:
                client_id = exe(
                    "INSERT INTO clients (nom,telephone,email,adresse,nb_commandes,total_depense) VALUES (?,?,?,?,1,?)",
                    (nom, telephone, email, adresse, total))

            # Commande
            cmd_id = exe("""
                INSERT INTO commandes
                (numero,client_id,client_nom,client_telephone,client_email,
                 client_adresse,type_livraison,statut,montant_total,notes,date_commande)
                VALUES (?,?,?,?,?,?,?,'nouvelle',?,?,datetime('now','localtime'))
            """, (numero, client_id, nom, telephone, email, adresse, livraison, total, notes))

            # Items + mise à jour stock
            for item in items:
                exe("""
                    INSERT INTO commande_items
                    (commande_id,produit_id,produit_nom,prix_unit,quantite,sous_total)
                    VALUES (?,?,?,?,?,?)
                """, (cmd_id, item['id'], item['nom'], item['prix'],
                      item['quantite'], item['prix'] * item['quantite']))
                exe("UPDATE produits SET quantite=MAX(0,quantite-?) WHERE id=?",
                    (item['quantite'], item['id']))

            session.pop('panier', None)
            return redirect(url_for('commande_confirmee', numero=numero))
        except Exception as ex:
            flash(f"Erreur lors de la commande : {ex}", "danger")

    return render_template('public/commander.html',
        items=items, total=total, nb_panier=_nb_panier())

@app.route('/commande/<numero>')
def commande_confirmee(numero):
    cmd = qry("SELECT * FROM commandes WHERE numero=?", (numero,), one=True)
    if not cmd:
        abort(404)
    items = qry("SELECT * FROM commande_items WHERE commande_id=?", (cmd['id'],))
    return render_template('public/confirmation.html',
        commande=cmd, items=items, nb_panier=_nb_panier())

@app.route('/suivi', methods=['GET', 'POST'])
def suivi_form():
    if request.method == 'POST':
        numero = request.form.get('numero', '').strip().upper()
        if numero:
            return redirect(url_for('suivi_commande', numero=numero))
        flash("Saisissez un numéro de commande.", "warning")
    return render_template('public/suivi_form.html', nb_panier=_nb_panier())

@app.route('/suivi/<numero>')
def suivi_commande(numero):
    cmd = qry("SELECT * FROM commandes WHERE numero=?", (numero,), one=True)
    if not cmd:
        flash("Commande introuvable. Vérifiez le numéro.", "danger")
        return redirect(url_for('suivi_form'))
    items = qry("SELECT * FROM commande_items WHERE commande_id=?", (cmd['id'],))
    return render_template('public/suivi.html',
        commande=cmd, items=items, nb_panier=_nb_panier())

# ═══════════════════════════════════════════════════════════════
# ADMIN — AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════
@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_dashboard') if 'admin_id' in session else url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        pwd   = request.form.get('password', '')
        user  = qry("SELECT * FROM utilisateurs WHERE login=?", (login,), one=True)
        if user and (check_password_hash(user['password'], pwd) or user['password'] == pwd):
            session.permanent = True
            session['admin_id']    = user['id']
            session['admin_nom']   = user['nom'] or user['login']
            session['admin_role']  = user['role']
            session['admin_login'] = user['login']
            flash(f"Bienvenue {session['admin_nom']} !", "success")
            return redirect(url_for('admin_dashboard'))
        flash("Identifiants incorrects.", "danger")
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    nom = session.get('admin_nom', '')
    session.clear()
    flash(f"À bientôt{', ' + nom if nom else ''} !", "info")
    return redirect(url_for('admin_login'))

# ─── DASHBOARD ───────────────────────────────────────────────
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    kpi_p  = qry("SELECT COUNT(*) as t, SUM(quantite*prix) as v FROM produits WHERE disponible=1", one=True)
    kpi_c  = qry("SELECT COUNT(*) as t FROM clients", one=True)
    kpi_cmd= qry("SELECT COUNT(*) as t FROM commandes WHERE statut!='annulée'", one=True)
    kpi_ca = qry("""
        SELECT COALESCE(SUM(montant_total),0) as ca FROM commandes
        WHERE statut!='annulée'
        AND strftime('%Y-%m',date_commande)=strftime('%Y-%m','now','localtime')
    """, one=True)
    nouvelles  = qry("SELECT COUNT(*) as n FROM commandes WHERE statut='nouvelle'", one=True)['n']

    # Commandes récentes
    commandes_recentes = qry("""
        SELECT c.*, COUNT(ci.id) as nb_items
        FROM commandes c
        LEFT JOIN commande_items ci ON c.id=ci.commande_id
        GROUP BY c.id ORDER BY c.date_commande DESC LIMIT 10
    """)

    # Alertes stock
    alertes_stock = qry("SELECT * FROM produits WHERE quantite<5 AND disponible=1 ORDER BY quantite LIMIT 8")

    # CA 6 derniers mois
    ca_mensuel = qry("""
        SELECT strftime('%m/%Y',date_commande) as mois,
               strftime('%Y%m',date_commande) as mois_sort,
               SUM(montant_total) as ca, COUNT(*) as nb
        FROM commandes WHERE statut!='annulée'
        AND date_commande>=date('now','-6 months','localtime')
        GROUP BY strftime('%Y-%m',date_commande)
        ORDER BY mois_sort ASC
    """)

    # Top produits
    top_produits = qry("""
        SELECT ci.produit_nom, SUM(ci.quantite) as total_vendu, SUM(ci.sous_total) as ca
        FROM commande_items ci
        JOIN commandes c ON ci.commande_id=c.id
        WHERE c.statut!='annulée'
        GROUP BY ci.produit_nom ORDER BY total_vendu DESC LIMIT 5
    """)

    # Répartition statuts
    statuts = qry("SELECT statut, COUNT(*) as nb FROM commandes GROUP BY statut")

    return render_template('admin/dashboard.html',
        kpi_p=kpi_p, kpi_c=kpi_c, kpi_cmd=kpi_cmd, kpi_ca=kpi_ca,
        nouvelles=nouvelles,
        commandes_recentes=commandes_recentes,
        alertes_stock=alertes_stock,
        ca_mensuel=ca_mensuel,
        top_produits=top_produits,
        statuts=statuts)

# ─── COMMANDES ───────────────────────────────────────────────
@app.route('/admin/commandes')
@login_required
def admin_commandes():
    sf = request.args.get('statut', '')
    sql = """
        SELECT c.*, COUNT(ci.id) as nb_items
        FROM commandes c LEFT JOIN commande_items ci ON c.id=ci.commande_id
        WHERE 1=1
    """
    args = []
    if sf:
        sql += " AND c.statut=?"; args.append(sf)
    sql += " GROUP BY c.id ORDER BY c.date_commande DESC"
    commandes = qry(sql, args)
    comptages = {r['statut']: r['nb'] for r in qry("SELECT statut, COUNT(*) as nb FROM commandes GROUP BY statut")}
    return render_template('admin/commandes.html',
        commandes=commandes, statut_filtre=sf, comptages=comptages)

@app.route('/admin/commande/<int:id>')
@login_required
def admin_commande_detail(id):
    cmd = qry("SELECT * FROM commandes WHERE id=?", (id,), one=True)
    if not cmd:
        flash("Commande introuvable.", "danger"); return redirect(url_for('admin_commandes'))
    items = qry("SELECT * FROM commande_items WHERE commande_id=?", (id,))
    return render_template('admin/commande_detail.html', commande=cmd, items=items)

@app.route('/admin/commande/<int:id>/statut', methods=['POST'])
@login_required
def admin_maj_statut(id):
    statuts_ok = ['nouvelle','confirmée','en_preparation','prête','livrée','annulée']
    nouveau = request.form.get('statut', '')
    if nouveau not in statuts_ok:
        flash("Statut invalide.", "danger"); return redirect(url_for('admin_commande_detail', id=id))
    exe("UPDATE commandes SET statut=? WHERE id=?", (nouveau, id))
    flash(f"✓ Statut mis à jour : {statut_label(nouveau)}", "success")
    return redirect(url_for('admin_commande_detail', id=id))

@app.route('/admin/facture/<int:cmd_id>')
@login_required
def admin_facture(cmd_id):
    cmd = qry("""
        SELECT c.*, cl.nom as client_nom_fiche, cl.telephone as client_tel_fiche,
               cl.email as client_email_fiche, cl.adresse as client_adresse_fiche
        FROM commandes c LEFT JOIN clients cl ON c.client_id=cl.id
        WHERE c.id=?
    """, (cmd_id,), one=True)
    if not cmd:
        flash("Commande introuvable.", "danger"); return redirect(url_for('admin_factures'))
    items = qry("SELECT * FROM commande_items WHERE commande_id=?", (cmd_id,))
    return render_template('admin/facture_print.html', commande=cmd, items=items)

@app.route('/admin/factures')
@login_required
def admin_factures():
    factures = qry("""
        SELECT c.id, c.numero, c.client_nom, c.montant_total, c.statut, c.date_commande
        FROM commandes c WHERE c.statut NOT IN ('annulée','nouvelle')
        ORDER BY c.date_commande DESC
    """)
    return render_template('admin/factures.html', factures=factures)

# ─── INVENTAIRE ──────────────────────────────────────────────
@app.route('/admin/inventaire')
@login_required
def admin_inventaire():
    cat = request.args.get('cat', '')
    q   = request.args.get('q', '')
    sql = "SELECT * FROM produits WHERE 1=1"
    args = []
    if cat:
        sql += " AND categorie=?"; args.append(cat)
    if q:
        sql += " AND (nom LIKE ? OR description_courte LIKE ?)"; args += [f'%{q}%', f'%{q}%']
    sql += " ORDER BY categorie, nom"
    produits = qry(sql, args)
    categories = [r['categorie'] for r in qry("SELECT DISTINCT categorie FROM produits ORDER BY categorie")]
    return render_template('admin/inventaire.html', produits=produits, categories=categories, cat=cat, q=q)

@app.route('/admin/produit/ajouter', methods=['GET', 'POST'])
@login_required
def admin_ajouter_produit():
    if request.method == 'POST':
        f = request.form
        exe("""
            INSERT INTO produits (nom,categorie,prix,quantite,description_courte,description,
                                  emoji,disponible,en_vedette,temps_prep)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (f['nom'], f['categorie'], float(f.get('prix',0)), int(f.get('quantite',0)),
              f.get('description_courte',''), f.get('description',''),
              f.get('emoji','🍽️'), 1 if f.get('disponible') else 0,
              1 if f.get('en_vedette') else 0, int(f.get('temps_prep',20))))
        flash(f"✓ Produit « {f['nom']} » ajouté !", "success")
        return redirect(url_for('admin_inventaire'))
    return render_template('admin/produit_form.html', produit=None)

@app.route('/admin/produit/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def admin_modifier_produit(id):
    produit = qry("SELECT * FROM produits WHERE id=?", (id,), one=True)
    if not produit:
        flash("Produit introuvable.", "danger"); return redirect(url_for('admin_inventaire'))
    if request.method == 'POST':
        f = request.form
        exe("""
            UPDATE produits SET nom=?,categorie=?,prix=?,quantite=?,
            description_courte=?,description=?,emoji=?,
            disponible=?,en_vedette=?,temps_prep=? WHERE id=?
        """, (f['nom'], f['categorie'], float(f.get('prix',0)), int(f.get('quantite',0)),
              f.get('description_courte',''), f.get('description',''),
              f.get('emoji','🍽️'), 1 if f.get('disponible') else 0,
              1 if f.get('en_vedette') else 0, int(f.get('temps_prep',20)), id))
        flash("✓ Produit mis à jour !", "success")
        return redirect(url_for('admin_inventaire'))
    return render_template('admin/produit_form.html', produit=produit)

@app.route('/admin/produit/<int:id>/supprimer')
@login_required
def admin_supprimer_produit(id):
    p = qry("SELECT nom FROM produits WHERE id=?", (id,), one=True)
    exe("UPDATE produits SET disponible=0 WHERE id=?", (id,))
    flash(f"✓ « {p['nom'] if p else id} » désactivé.", "success")
    return redirect(url_for('admin_inventaire'))

# ─── CLIENTS ─────────────────────────────────────────────────
@app.route('/admin/clients')
@login_required
def admin_clients():
    q = request.args.get('q', '')
    sql = "SELECT * FROM clients WHERE 1=1"
    args = []
    if q:
        sql += " AND (nom LIKE ? OR telephone LIKE ? OR email LIKE ?)"; args += [f'%{q}%']*3
    sql += " ORDER BY total_depense DESC, nom ASC"
    return render_template('admin/clients.html', clients=qry(sql, args), q=q)

@app.route('/admin/client/<int:id>')
@login_required
def admin_client_detail(id):
    client = qry("SELECT * FROM clients WHERE id=?", (id,), one=True)
    if not client:
        flash("Client introuvable.", "danger"); return redirect(url_for('admin_clients'))
    commandes = qry("SELECT * FROM commandes WHERE client_id=? ORDER BY date_commande DESC", (id,))
    return render_template('admin/client_detail.html', client=client, commandes=commandes)

@app.route('/admin/client/ajouter', methods=['GET', 'POST'])
@login_required
def admin_ajouter_client():
    if request.method == 'POST':
        f = request.form
        exe("INSERT INTO clients (nom,telephone,email,adresse,type_client) VALUES (?,?,?,?,?)",
            (f['nom'], f.get('telephone',''), f.get('email',''), f.get('adresse',''), f.get('type_client','particulier')))
        flash(f"✓ Client « {f['nom']} » ajouté !", "success")
        return redirect(url_for('admin_clients'))
    return render_template('admin/client_form.html', client=None)

@app.route('/admin/client/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def admin_modifier_client(id):
    client = qry("SELECT * FROM clients WHERE id=?", (id,), one=True)
    if not client:
        flash("Client introuvable.", "danger"); return redirect(url_for('admin_clients'))
    if request.method == 'POST':
        f = request.form
        exe("UPDATE clients SET nom=?,telephone=?,email=?,adresse=?,type_client=? WHERE id=?",
            (f['nom'], f.get('telephone',''), f.get('email',''), f.get('adresse',''), f.get('type_client','particulier'), id))
        flash("✓ Client mis à jour !", "success")
        return redirect(url_for('admin_clients'))
    return render_template('admin/client_form.html', client=client)

# ─── FOURNISSEURS ─────────────────────────────────────────────
@app.route('/admin/fournisseurs')
@login_required
def admin_fournisseurs():
    q = request.args.get('q', '')
    sql = "SELECT * FROM fournisseurs WHERE 1=1"
    args = []
    if q:
        sql += " AND (nom_societe LIKE ? OR contact LIKE ?)"; args += [f'%{q}%']*2
    sql += " ORDER BY nom_societe"
    return render_template('admin/fournisseurs.html', fournisseurs=qry(sql, args), q=q)

@app.route('/admin/fournisseur/ajouter', methods=['GET', 'POST'])
@login_required
def admin_ajouter_fournisseur():
    if request.method == 'POST':
        f = request.form
        exe("INSERT INTO fournisseurs (nom_societe,contact,telephone,email,adresse) VALUES (?,?,?,?,?)",
            (f['nom_societe'], f.get('contact',''), f.get('telephone',''), f.get('email',''), f.get('adresse','')))
        flash(f"✓ Fournisseur « {f['nom_societe']} » ajouté !", "success")
        return redirect(url_for('admin_fournisseurs'))
    return render_template('admin/fournisseur_form.html', fournisseur=None)

@app.route('/admin/fournisseur/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def admin_modifier_fournisseur(id):
    fournisseur = qry("SELECT * FROM fournisseurs WHERE id=?", (id,), one=True)
    if not fournisseur:
        flash("Fournisseur introuvable.", "danger"); return redirect(url_for('admin_fournisseurs'))
    if request.method == 'POST':
        f = request.form
        exe("UPDATE fournisseurs SET nom_societe=?,contact=?,telephone=?,email=?,adresse=? WHERE id=?",
            (f['nom_societe'], f.get('contact',''), f.get('telephone',''), f.get('email',''), f.get('adresse',''), id))
        flash("✓ Fournisseur mis à jour !", "success")
        return redirect(url_for('admin_fournisseurs'))
    return render_template('admin/fournisseur_form.html', fournisseur=fournisseur)

@app.route('/admin/fournisseur/<int:id>/supprimer')
@login_required
def admin_supprimer_fournisseur(id):
    f = qry("SELECT nom_societe FROM fournisseurs WHERE id=?", (id,), one=True)
    exe("DELETE FROM fournisseurs WHERE id=?", (id,))
    flash(f"✓ Fournisseur « {f['nom_societe'] if f else id} » supprimé.", "success")
    return redirect(url_for('admin_fournisseurs'))

# ─── API JSON ─────────────────────────────────────────────────
@app.route('/admin/api/stats')
@login_required
def api_stats():
    ca_data = qry("""
        SELECT strftime('%m/%Y',date_commande) as mois,
               strftime('%Y%m',date_commande) as tri,
               COALESCE(SUM(montant_total),0) as ca, COUNT(*) as nb
        FROM commandes WHERE statut!='annulée'
        AND date_commande>=date('now','-6 months','localtime')
        GROUP BY strftime('%Y-%m',date_commande)
        ORDER BY tri ASC
    """)
    statuts = qry("SELECT statut, COUNT(*) as nb FROM commandes GROUP BY statut")
    return jsonify({'ca': ca_data, 'statuts': statuts})

@app.route('/api/produits')
def api_produits():
    return jsonify(qry("SELECT id,nom,prix,emoji,categorie FROM produits WHERE disponible=1 ORDER BY nom"))

# ─── ERREURS ─────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('public/404.html', nb_panier=_nb_panier()), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('public/404.html', nb_panier=_nb_panier(),
                           titre="Erreur serveur", msg="Une erreur interne s'est produite."), 500

# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    # Import et initialisation BDD au démarrage si pas encore faite
    from init_db import init_db
    with app.app_context():
        init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
