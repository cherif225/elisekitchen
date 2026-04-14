"""
init_db.py — Crée la base SQLite et insère les données de démonstration.
Lancez directement : python init_db.py
Ou appelé automatiquement au premier démarrage de app.py
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'chegest.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS utilisateurs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    login    TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    nom      TEXT,
    email    TEXT,
    role     TEXT DEFAULT 'caisse',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS produits (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nom               TEXT NOT NULL,
    categorie         TEXT NOT NULL DEFAULT 'Restaurant',
    prix              REAL NOT NULL DEFAULT 0,
    quantite          INTEGER NOT NULL DEFAULT 0,
    description       TEXT,
    description_courte TEXT,
    emoji             TEXT DEFAULT '🍽️',
    disponible        INTEGER DEFAULT 1,
    en_vedette        INTEGER DEFAULT 0,
    temps_prep        INTEGER DEFAULT 20,
    created_at        TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS clients (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nom            TEXT NOT NULL,
    telephone      TEXT,
    email          TEXT,
    adresse        TEXT,
    type_client    TEXT DEFAULT 'particulier',
    nb_commandes   INTEGER DEFAULT 0,
    total_depense  REAL DEFAULT 0,
    created_at     TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS fournisseurs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_societe TEXT NOT NULL,
    contact     TEXT,
    telephone   TEXT,
    email       TEXT,
    adresse     TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS commandes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    numero           TEXT UNIQUE NOT NULL,
    client_id        INTEGER,
    client_nom       TEXT NOT NULL,
    client_telephone TEXT NOT NULL,
    client_email     TEXT,
    client_adresse   TEXT,
    type_livraison   TEXT DEFAULT 'retrait',
    statut           TEXT DEFAULT 'nouvelle',
    montant_total    REAL NOT NULL DEFAULT 0,
    notes            TEXT,
    date_commande    TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS commande_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    commande_id INTEGER NOT NULL,
    produit_id  INTEGER,
    produit_nom TEXT NOT NULL,
    prix_unit   REAL NOT NULL,
    quantite    INTEGER NOT NULL DEFAULT 1,
    sous_total  REAL NOT NULL,
    FOREIGN KEY (commande_id) REFERENCES commandes(id) ON DELETE CASCADE,
    FOREIGN KEY (produit_id)  REFERENCES produits(id)  ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_commandes_statut ON commandes(statut);
CREATE INDEX IF NOT EXISTS idx_commandes_date   ON commandes(date_commande);
CREATE INDEX IF NOT EXISTS idx_produits_cat     ON produits(categorie, disponible);
"""

UTILISATEURS = [
    ('admin',  'Fogue@2026',   'Fogue Deyo Delphine',      'admin@elisekitchen.ci',  'admin'),
    ('gerant', 'Fogue@2026',  'Fogue Deyo Delphine',          'gerant@elisekitchen.ci', 'gerant'),
    ('caisse', 'Fogue@2026',  'Fogue Deyo Delphine',   'caisse@elisekitchen.ci', 'caisse'),
]

PRODUITS = [
    # (nom, categorie, prix, quantite, desc_courte, description, emoji, en_vedette, temps_prep)
    ('Poulet Braisé Signature',  'Restaurant', 4500, 30,
     'Notre spécialité braisée aux épices maison',
     'Poulet entier mariné 24h et braisé sur braise vive avec notre mélange d\'épices secret. Servi avec attiéké ou riz selon votre choix.',
     '🍗', 1, 35),
    ('Kedjenou de Poulet',       'Restaurant', 3500, 25,
     'Mijoté traditionnel en cocotte ivoirienne',
     'Plat emblématique de la cuisine ivoirienne : poulet mijoté avec légumes frais dans une sauce épicée en poterie. Authenticité garantie.',
     '🫕', 1, 45),
    ('Attiéké Poisson Braisé',   'Restaurant', 2500, 40,
     'Attiéké frais artisanal + poisson capitaine grillé',
     'Le duo incontournable : attiéké pressé artisanalement, servi avec un poisson capitaine braisé doré, sauce tomate et piment maison.',
     '🐟', 1, 25),
    ('Alloco + Poisson Frit',    'Restaurant', 2000, 50,
     'Bananes plantains frites dorées',
     'Bananes plantains bien mûres frites à la perfection, accompagnées de poisson frit croustillant et notre sauce piment signature.',
     '🍌', 0, 20),
    ('Riz Sauce Graine',         'Restaurant', 2000, 35,
     'Riz blanc + sauce graine cuite à l\'ancienne',
     'Riz blanc cuit à point, nappé de notre sauce graine (huile de palme) préparée à l\'ancienne avec viande de bœuf et légumes du marché.',
     '🍚', 0, 30),
    ('Garba Spécial',            'Restaurant', 1500, 60,
     'Attiéké + thon au poivre, le classique populaire',
     'Le plat populaire par excellence en Côte d\'Ivoire : attiéké granuleux mélangé avec thon au poivre, oignons et tomates fraîches.',
     '🥘', 0, 15),
    ('Foutou Banane + Sauce',    'Restaurant', 2500, 20,
     'Foutou de banane pilé tradition',
     'Foutou de banane pilé à la tradition, servi avec sauce graine ou sauce arachide maison, accompagné de viande de votre choix.',
     '🫙', 0, 40),
    ('Soupe Légumes du Marché',  'Restaurant', 1500, 20,
     'Soupe fraîche aux légumes locaux de saison',
     'Soupe réconfortante préparée avec les légumes frais du marché local, épices douces, morceaux de bœuf et herbes aromatiques.',
     '🥗', 0, 25),
    ('Jus de Bissap Maison',     'Boissons',    500, 80,
     'Fleurs d\'hibiscus fraîches, sucré naturel',
     'Jus artisanal de fleurs d\'hibiscus séchées préparé chaque matin. Légèrement sucré, très rafraîchissant. Sans conservateurs.',
     '🍹', 1, 5),
    ('Jus de Gingembre Frais',   'Boissons',    600, 60,
     'Gingembre pressé, citron, miel — tonique',
     'Boisson tonique préparée avec gingembre frais pressé, jus de citron et miel naturel. Idéal pour stimuler l\'immunité.',
     '🫚', 0, 5),
    ('Jus d\'Orange Pressé',     'Boissons',    700, 45,
     'Oranges locales pressées à la commande',
     'Jus d\'oranges locales pressées à la commande. 100% naturel, sans sucre ajouté, sans conservateurs.',
     '🍊', 0, 5),
    ('Eau Minérale 1.5L',        'Boissons',    300, 120,
     'Eau minérale fraîche, plate',
     'Eau minérale fraîche servie bien glacée.',
     '💧', 0, 1),
    ('Piment Séché en Poudre',   'Épicerie',    200, 40,
     'Piment local très fort, moulu artisanalement',
     'Piment séché et moulu artisanalement. Extra fort, idéal pour relever les sauces et marinades locales.',
     '🌶️', 0, 1),
    ('Huile de Palme Rouge 1L',  'Épicerie',    900, 15,
     'Huile palme pure non raffinée',
     'Huile de palme 100% naturelle, pressée à froid. Riche en nutriments, indispensable pour les sauces locales authentiques.',
     '🫙', 0, 1),
    ('Attiéké Cru 500g',         'Épicerie',    800, 30,
     'Attiéké artisanal prêt à cuire en 10 min',
     'Attiéké artisanal préparé par nos femmes transformatrices locales. Granuleux, frais et prêt à cuire en seulement 10 minutes.',
     '🌾', 0, 1),
    ('Sucre Blanc 1kg',          'Épicerie',    600,  8,
     'Sucre cristallisé blanc',
     'Sucre blanc cristallisé de qualité supérieure.',
     '🍬', 0, 1),
    ('Riz Local Parfumé 5kg',    'Épicerie',   2500, 20,
     'Riz local à grain long naturellement parfumé',
     'Riz local cultivé localement, grain long naturellement parfumé. Goût authentique et texture parfaite.',
     '🌾', 0, 1),
    ('Concentré de Tomate 400g', 'Épicerie',    450, 35,
     'Double concentré de tomate importé',
     'Concentré de tomate double, idéal pour les sauces et ragoûts locaux.',
     '🍅', 0, 1),
]

CLIENTS = [
    ('Koffi Ange',           '+225 07 00 11 22', 'koffi.ange@email.ci',      'Cocody, Abidjan',         'vip',          8, 45000),
    ('Akoua Mbeki',          '+225 05 44 33 21', 'akoua.mbeki@gmail.com',    'Yopougon, Abidjan',       'particulier',  3, 12500),
    ('Restaurant Le Bleu',   '+225 27 00 55 66', 'contact@lebleu.ci',        'Zone 4, Abidjan',         'professionnel',12,125000),
    ('Jean-Paul Kouassi',    '+225 01 99 88 77', 'jp.kouassi@yahoo.fr',      'Plateau, Abidjan',        'particulier',  2,  9000),
    ('Marie Traoré',         '+225 05 11 22 44', 'marie.traore@outlook.com', 'Marcory, Abidjan',        'particulier',  5, 18500),
    ('Hôtel Ivoire Events',  '+225 27 20 01 00', 'events@hotelroyalvoire.ci','Cocody, Abidjan',         'professionnel', 6,280000),
]

FOURNISSEURS = [
    ('Grossiste Alimentaire SACI', 'M. Kouassi Yao',   '+225 27 20 10 00', 'saci@gmail.com',        'Zone Industrielle, Abidjan'),
    ('Ferme Avicole du Plateau',   'Mme Aissatou Bah', '+225 07 66 77 88', 'ferme.plateau@ci.com',  'Yamoussoukro'),
    ('SOLIBRA - Boissons',         'M. Pierre Gnagne', '+225 27 35 20 00', 'commercial@solibra.ci', 'Yopougon, Abidjan'),
    ('Marché de Gros Adjamé',      'Mme Clémentine',   '+225 07 33 11 55', 'mgo.adjame@email.ci',   'Adjamé, Abidjan'),
]

def init_db(db_path=None):
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Ne pas réinitialiser si la base existe déjà
    db_exists = os.path.exists(path) and os.path.getsize(path) > 0
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    conn.commit()

    if db_exists:
        # Vérifier si déjà peuplé
        count = conn.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0]
        if count > 0:
            conn.close()
            return

    print("  → Création des données initiales...")

    # Utilisateurs
    for login, pwd, nom, email, role in UTILISATEURS:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO utilisateurs (login,password,nom,email,role) VALUES (?,?,?,?,?)",
                (login, generate_password_hash(pwd), nom, email, role))
        except Exception:
            pass

    # Produits
    for nom, cat, prix, qty, desc_c, desc, emoji, vedette, tprep in PRODUITS:
        conn.execute("""
            INSERT INTO produits (nom,categorie,prix,quantite,description_courte,description,
                                  emoji,disponible,en_vedette,temps_prep)
            VALUES (?,?,?,?,?,?,?,1,?,?)
        """, (nom, cat, prix, qty, desc_c, desc, emoji, vedette, tprep))

    # Clients
    for nom, tel, email, adr, type_c, nb_cmd, total in CLIENTS:
        conn.execute("""
            INSERT INTO clients (nom,telephone,email,adresse,type_client,nb_commandes,total_depense)
            VALUES (?,?,?,?,?,?,?)
        """, (nom, tel, email, adr, type_c, nb_cmd, total))

    # Fournisseurs
    for soc, contact, tel, email, adr in FOURNISSEURS:
        conn.execute(
            "INSERT INTO fournisseurs (nom_societe,contact,telephone,email,adresse) VALUES (?,?,?,?,?)",
            (soc, contact, tel, email, adr))

    # Commandes exemples
    from datetime import datetime, timedelta
    now = datetime.now()

    commandes_data = [
        ('CMD-DEMO-0001', 1, 'Koffi Ange',          '+225 07 00 11 22', 'koffi@email.ci',    'retrait',   'livrée',          9000, now - timedelta(days=3)),
        ('CMD-DEMO-0002', 2, 'Akoua Mbeki',          '+225 05 44 33 21', 'akoua@gmail.com',   'livraison', 'livrée',          5500, now - timedelta(days=2)),
        ('CMD-DEMO-0003', 3, 'Restaurant Le Bleu',   '+225 27 00 55 66', 'contact@lebleu.ci', 'livraison', 'confirmée',      22500, now - timedelta(days=1)),
        ('CMD-DEMO-0004', None,'Client Passage',     '+225 07 99 00 11', None,                'retrait',   'en_preparation',  4500, now - timedelta(hours=2)),
        ('CMD-DEMO-0005', None,'Amara Diallo',        '+225 01 55 66 77', 'amara@email.com',   'retrait',   'nouvelle',        3000, now - timedelta(minutes=25)),
    ]
    for numero, cid, cnom, ctel, cemail, livr, statut, montant, date in commandes_data:
        conn.execute("""
            INSERT INTO commandes
            (numero,client_id,client_nom,client_telephone,client_email,type_livraison,statut,montant_total,date_commande)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (numero, cid, cnom, ctel, cemail, livr, statut, montant, date.strftime('%Y-%m-%d %H:%M:%S')))

    # Items pour les commandes démo
    cmd_ids = [r[0] for r in conn.execute("SELECT id FROM commandes ORDER BY id").fetchall()]
    if len(cmd_ids) >= 5:
        items_data = [
            (cmd_ids[0], 1, 'Poulet Braisé Signature', 4500, 2),
            (cmd_ids[1], 3, 'Attiéké Poisson Braisé',  2500, 1),
            (cmd_ids[1], 9, 'Jus de Bissap Maison',     500, 2),
            (cmd_ids[1], 4, 'Alloco + Poisson Frit',   2000, 1),
            (cmd_ids[2], 1, 'Poulet Braisé Signature', 4500, 5),
            (cmd_ids[3], 1, 'Poulet Braisé Signature', 4500, 1),
            (cmd_ids[4], 6, 'Garba Spécial',           1500, 2),
        ]
        for cid, pid, pnom, pu, qty in items_data:
            conn.execute("""
                INSERT INTO commande_items (commande_id,produit_id,produit_nom,prix_unit,quantite,sous_total)
                VALUES (?,?,?,?,?,?)
            """, (cid, pid, pnom, pu, qty, pu*qty))

    conn.commit()
    conn.close()
    print("  ✅ Base de données initialisée avec succès !")


if __name__ == '__main__':
    print("\n🔧 Initialisation de la base de données ELISE KITCHEN\n" + "─"*50)
    init_db()
    print("\n🔑 Identifiants de connexion :")
    for login, pwd, _, _, role in UTILISATEURS:
        print(f"   {role:<8} → login: {login:<10} | mot de passe: {pwd}")
    print(f"\n📁 Base créée : {DB_PATH}")
    print("\n🚀 Lancez l'application : python app.py")
    print("   Site client  → http://localhost:5000/")
    print("   Administration → http://localhost:5000/admin\n")
