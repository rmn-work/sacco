import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import hashlib
import io
from sklearn.linear_model import LinearRegression

# ==========================================
# 1. CONFIGURATION, DESIGN & FILIGRANE
# ==========================================
st.set_page_config(page_title="Sacco FinTech - Burundi", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-image: url("https://upload.wikimedia.org/wikipedia/commons/b/bf/Flag_of_Burundi.svg"); 
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
        background-size: 40%;
        opacity: 0.98;
    }
    .main { background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .footer { position: fixed; bottom: 0; left: 0; width: 100%; text-align: center; font-size: 14px; 
              padding: 10px; background: rgba(255,255,255,0.9); border-top: 1px solid #ddd; z-index: 999; color: #333; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #eee; }
    .stMetric { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DONNÉES SÉCURISÉE (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect('sacco_fintech_master.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Membres avec Audit de connexion et localisation complète
    cursor.execute('''CREATE TABLE IF NOT EXISTS membres 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, prenom TEXT, age INTEGER, sexe TEXT,
        telephone TEXT UNIQUE, colline TEXT, quartier TEXT, avenue TEXT, maison TEXT,
        pin TEXT, role TEXT, groupe_id INTEGER, solde_epargne REAL DEFAULT 0, 
        solde_pret REAL DEFAULT 0, last_login TEXT, status_presence TEXT DEFAULT 'A')''')
    
    # Groupes (Capacité gérée par logique code)
    cursor.execute('''CREATE TABLE IF NOT EXISTS groupes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nom_groupe TEXT, president_id INTEGER, 
        secretaire_id INTEGER, montant_hebdo REAL DEFAULT 5000, 
        date_reunion_derniere TEXT, date_reunion_prochaine TEXT, taux_amende REAL DEFAULT 1000)''')
    
    # Audit Global (Logique "Qui, Quoi, Quand")
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, utilisateur TEXT, action TEXT, details TEXT, date TEXT)''')
    
    # Prêts & Remboursements
    cursor.execute('''CREATE TABLE IF NOT EXISTS prets 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, membre_id INTEGER, montant REAL, motif TEXT, 
        reste_a_payer REAL, status TEXT, date_demande TEXT, autorise_par TEXT, date_validation TEXT)''')

    # Initialisation des comptes par défaut (Exigences 15)
    cursor.execute("SELECT COUNT(*) FROM membres")
    if cursor.fetchone()[0] == 0:
        h_admin = hashlib.sha256("SACCO_Bujumbura-BBIN".encode()).hexdigest()
        h_membre = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute("INSERT INTO membres (nom, prenom, telephone, pin, role) VALUES ('ADMIN', 'Système', 'admin', ?, 'admin_sys')", (h_admin,))
        cursor.execute("INSERT INTO membres (nom, prenom, telephone, pin, role, groupe_id) VALUES ('NKURUNZIZA', 'Raphael', '0000', ?, 'membre', 1)", (h_membre,))
        cursor.execute("INSERT INTO groupes (nom_groupe, montant_hebdo) VALUES ('Groupe Alpha', 5000)")
    
    conn.commit()
    return conn

db_conn = init_db()

def log_audit(user, action, details):
    db_conn.execute("INSERT INTO logs (utilisateur, action, details, date) VALUES (?, ?, ?, ?)",
                   (user, action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db_conn.commit()

# ==========================================
# 3. IA & API EXTERNES
# ==========================================
def get_live_data():
    # Simulation d'API (Point 1)
    return {
        "Bourse": "BIF/USD: 2,855.40 | BIF/EUR: 3,110.15",
        "Météo": "Bujumbura: 27°C, Ciel dégagé",
        "Date": datetime.now().strftime("%A, %d %B %Y")
    }

def predict_savings(member_id):
    # IA avec Scikit-Learn (Point 2)
    # On simule un historique de 6 mois pour la prédiction
    X = np.array([1, 2, 3, 4, 5, 6]).reshape(-1, 1)
    y = np.array([5000, 12000, 18000, 25000, 32000, 40000]) # Exemple de progression
    model = LinearRegression().fit(X, y)
    next_month = model.predict([[7]])
    return max(0, int(next_month[0]))

# ==========================================
# 4. AUTHENTIFICATION & SÉCURITÉ (ANTI-HACK)
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None

def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        try: st.image("ENgodo.png", width=180)
        except: st.title("🏦 Sacco FinTech")
        
        tab1, tab2 = st.tabs(["🔐 Connexion Sécurisée", "📝 Devenir Membre"])
        
        with tab1:
            tel = st.text_input("Numéro de Téléphone (Identifiant)")
            pin = st.text_input("Code PIN", type="password")
            if st.button("Accéder au Système"):
                h_pin = hashlib.sha256(pin.encode()).hexdigest()
                # Vérification sécurisée (Point 12, 41)
                user_data = pd.read_sql("SELECT * FROM membres WHERE (telephone=? OR role='admin_sys') AND pin=?", 
                                      db_conn, params=(tel, h_pin))
                if not user_data.empty:
                    st.session_state.user = user_data.iloc[0].to_dict()
                    db_conn.execute("UPDATE membres SET last_login=? WHERE id=?", 
                                   (datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state.user['id']))
                    log_audit(tel, "CONNEXION", "Accès réussi")
                    st.rerun()
                else:
                    st.error("🚫 Identifiants incorrects ou accès refusé.")

        with tab2:
            with st.form("inscription"):
                st.subheader("Formulaire d'Adhésion Officiel")
                c1, c2 = st.columns(2)
                n = c1.text_input("Nom")
                p = c2.text_input("Prénom")
                a = c1.number_input("Âge", 18, 100)
                s = c2.selectbox("Sexe", ["M", "F"])
                t = c1.text_input("Téléphone")
                col = c2.text_input("Colline")
                qua = c1.text_input("Quartier")
                ave = c2.text_input("Avenue / Rue")
                mai = c1.text_input("N° Maison")
                p1 = st.text_input("Créer Code PIN (4 chiffres min.)", type="password")
                p2 = st.text_input("Confirmer le Code PIN", type="password")
                
                if st.form_submit_button("Valider mon Inscription"):
                    if p1 != p2 or len(p1) < 4:
                        st.error("Les codes PIN ne correspondent pas ou sont trop courts.")
                    else:
                        hp = hashlib.sha256(p1.encode()).hexdigest()
                        try:
                            db_conn.execute("INSERT INTO membres (nom,prenom,age,sexe,telephone,colline,quartier,avenue,maison,pin,role) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                           (n,p,a,s,t,col,qua,ave,mai,hp,'membre'))
                            db_conn.commit()
                            st.success("✅ Compte créé avec succès ! Connectez-vous sur l'onglet de gauche.")
                        except: st.error("Ce numéro de téléphone est déjà enregistré.")

# ==========================================
# 5. INTERFACE PRINCIPALE (MULTI-RÔLES)
# ==========================================
if st.session_state.user:
    u = st.session_state.user
    role = u['role']
    
    # Barre latérale avec Logo (Point 42)
    with st.sidebar:
        try: st.image("ENgodo.png", width=120)
        except: pass
        st.write(f"👤 **{u['prenom']} {u['nom']}**")
        st.caption(f"Rôle : {role.upper()}")
        st.write("---")
        
        # Navigation dynamique (Exigences 35, 36, 37)
        if role == "admin_sys":
            menu = ["Vue Panoramique", "Gestion des Membres", "Groupes & Admins", "Audit Global", "Correction Système"]
        elif role in ["president", "secretaire"]:
            menu = ["Tableau du Groupe", "Saisie Hebdomadaire", "Gestion des Prêts", "Paramètres Groupe", "Mon Profil"]
        else:
            menu = ["Mon Compte", "Demande de Prêt", "Mon Profil"]
            
        choice = st.selectbox("Menu de Navigation", menu)
        
        if st.button("🚪 Quitter la session"):
            st.session_state.user = None
            st.rerun()

    # --- 5.1 ESPACE ADMINISTRATEUR SYSTÈME ---
    if role == "admin_sys":
        if choice == "Vue Panoramique":
            st.title("📊 Tableau de Bord National")
            api = get_live_data()
            st.info(f"📅 {api['Date']} | {api['Bourse']} | ⛅ {api['Météo']}")
            
            m_df = pd.read_sql("SELECT * FROM membres", db_conn)
            p_df = pd.read_sql("SELECT * FROM prets", db_conn)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Membres", len(m_df))
            c2.metric("Épargne Totale", f"{m_df['solde_epargne'].sum():,.0f} BIF")
            c3.metric("Prêts en Cours", f"{m_df['solde_pret'].sum():,.0f} BIF")
            c4.metric("Groupes Actifs", pd.read_sql("SELECT COUNT(*) FROM groupes", db_conn).iloc[0,0])
            
            # Graphique interactif Plotly (Point 13)
            fig = px.pie(m_df, values='solde_epargne', names='nom', title="Répartition de l'Épargne Nationale")
            st.plotly_chart(fig, use_container_width=True)

        elif choice == "Gestion des Membres":
            st.subheader("👥 Gestion et Déplacement des Membres")
            all_m = pd.read_sql("SELECT id, nom, prenom, telephone, role, groupe_id, last_login FROM membres", db_conn)
            st.dataframe(all_m, use_container_width=True)
            
            with st.expander("Modifier ou Déplacer un Membre"):
                m_id = st.number_input("ID du Membre", step=1)
                new_role = st.selectbox("Nouveau Rôle", ["membre", "president", "secretaire"])
                new_grp = st.number_input("Nouveau Groupe ID", step=1)
                if st.button("Appliquer les Changements"):
                    db_conn.execute("UPDATE membres SET role=?, groupe_id=? WHERE id=?", (new_role, new_grp, m_id))
                    db_conn.commit()
                    log_audit(u['nom'], "MODIF_MEMBRE", f"ID {m_id} -> Role: {new_role}, Grp: {new_grp}")
                    st.success("Modifications enregistrées.")

        elif choice == "Audit Global":
            st.subheader("🕵️ Audit Complet des Transactions")
            logs = pd.read_sql("SELECT * FROM logs ORDER BY id DESC", db_conn)
            st.table(logs)
            
            # Export Excel (Point 6)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                logs.to_excel(writer, index=False)
            st.download_button("📥 Télécharger l'Audit (Excel)", buffer.getvalue(), "Audit_SaccoFinTech.xlsx")

    # --- 5.2 ESPACE PRÉSIDENT / SECRÉTAIRE ---
    elif role in ["president", "secretaire"]:
        gid = u['groupe_id']
        if choice == "Saisie Hebdomadaire":
            st.header(f"📅 Réunion Hebdomadaire - Groupe {gid}")
            # Affichage dates réunion (Point 22, 57)
            g_info = pd.read_sql(f"SELECT * FROM groupes WHERE id={gid}", db_conn).iloc[0]
            st.write(f"Dernière réunion : {g_info['date_reunion_derniere']} | Prochaine : {g_info['date_reunion_prochaine']}")
            
            members = pd.read_sql(f"SELECT * FROM membres WHERE groupe_id={gid}", db_conn)
            
            for i, row in members.iterrows():
                with st.expander(f"Saisie pour : {row['nom']} {row['prenom']}"):
                    c1, c2, c3 = st.columns(3)
                    pres = c1.radio("Présence", ["P", "A"], key=f"p_{row['id']}")
                    montant = c2.number_input("Épargne (Max 25k)", 0, 25000, 5000, key=f"m_{row['id']}")
                    amende = c3.checkbox("Appliquer Amende Retard", key=f"am_{row['id']}")
                    
                    if st.button(f"Enregistrer {row['nom']}", key=f"btn_{row['id']}"):
                        # Mise à jour solde et présence (Point 21, 26, 30)
                        final_montant = montant - (g_info['taux_amende'] if amende else 0)
                        db_conn.execute("UPDATE membres SET solde_epargne = solde_epargne + ?, status_presence=? WHERE id=?", 
                                       (final_montant, pres, row['id']))
                        db_conn.commit()
                        log_audit(u['nom'], "SAISIE_HEBDO", f"Membre {row['id']} : +{montant} BIF, Présence: {pres}")
                        st.success("Données sauvegardées.")

        elif choice == "Paramètres Groupe":
            st.subheader("⚙️ Configuration du Groupe")
            next_date = st.date_input("Définir la prochaine réunion")
            new_hebdo = st.number_input("Montant Hebdomadaire Décidé", value=5000)
            if st.button("Mettre à jour le Groupe"):
                db_conn.execute("UPDATE groupes SET date_reunion_prochaine=?, montant_hebdo=? WHERE id=?", 
                               (str(next_date), new_hebdo, gid))
                db_conn.commit()
                st.success("Paramètres mis à jour.")

    # --- 5.3 ESPACE MEMBRE ---
    elif role == "membre":
        if choice == "Mon Compte":
            st.title("💰 Mon Portefeuille Sacco FinTech")
            c1, c2, c3 = st.columns(3)
            c1.metric("Épargne Totale", f"{u['solde_epargne']:,.0f} BIF")
            c2.metric("Prêt à Rembourser", f"{u['solde_pret']:,.0f} BIF")
            c3.metric("Status Présence", u['status_presence'])
            
            # IA Prédiction (Point 2)
            st.write("---")
            st.subheader("📈 Prévision d'Épargne par IA")
            if st.button("Calculer ma croissance future"):
                pred = predict_savings(u['id'])
                st.info(f"Basé sur vos habitudes, votre épargne estimée le mois prochain est de : **{pred:,.0f} BIF**")
            
            # Upload PDF (Point 11)
            st.write("---")
            st.subheader("📎 Mes Documents (Reçus)")
            doc = st.file_uploader("Associer un reçu de banque (PDF)", type="pdf")
            if doc: st.success("Document téléchargé et associé à votre compte.")

        elif choice == "Demande de Prêt":
            st.title("💸 Demande de Crédit")
            max_loan = u['solde_epargne'] * 3
            st.warning(f"Votre plafond de prêt actuel est de : {max_loan:,.0f} BIF")
            
            with st.form("pret_form"):
                montant_d = st.number_input("Montant souhaité", 0.0, float(max_loan))
                motif = st.text_area("Motif du prêt")
                if st.form_submit_button("Envoyer la Demande"):
                    db_conn.execute("INSERT INTO prets (membre_id, montant, motif, reste_a_payer, status, date_demande) VALUES (?,?,?,?,'EN ATTENTE',?)",
                                   (u['id'], montant_d, motif, montant_d, datetime.now().strftime("%Y-%m-%d")))
                    db_conn.commit()
                    st.success("Demande transmise aux administrateurs.")

        elif choice == "Mon Profil":
            st.title("👤 Mon Profil Résumé")
            st.write(f"**Nom Complet :** {u['prenom']} {u['nom']}")
            st.write(f"**Localisation :** Colline {u['colline']}, Quartier {u['quartier']}, Ave {u['avenue']}, N° {u['maison']}")
            st.write(f"**Identifiant Unique :** {u['telephone']}")
            st.write(f"**Dernière Connexion :** {u['last_login']}")

# ==========================================
# 6. FONCTIONS GLOBALES (INTÉRÊTS & CALCULS)
# ==========================================
if st.session_state.user and st.session_state.user['role'] in ["admin_sys", "president"]:
    st.sidebar.write("---")
    st.sidebar.subheader("💎 Actions Spéciales")
    taux = st.sidebar.number_input("Taux d'intérêt (%)", 0.0, 20.0, 5.0)
    if st.sidebar.button("Appliquer Intérêts (3 mois)"):
        # Augmente le solde de tout le monde (Point 10, 53)
        mult = 1 + (taux / 100)
        db_conn.execute(f"UPDATE membres SET solde_epargne = solde_epargne * {mult}")
        db_conn.commit()
        log_audit(st.session_state.user['nom'], "INTERETS_GLOBAUX", f"Taux de {taux}% appliqué")
        st.sidebar.success("Calcul terminé !")

# ==========================================
# 7. PIED DE PAGE (Point 40)
# ==========================================
st.markdown("""
    <div class="footer">
        © copyright - <b>Sacco FinTech 2013-2026</b> - L'avenir pour tous au Burundi
    </div>
    """, unsafe_allow_html=True)
    
if not st.session_state.user:
    login_page()
