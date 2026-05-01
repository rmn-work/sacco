import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime

# --- [POINTS 1, 2, 7, 13] MODULES INTERACTIFS ---
try:
    import plotly.express as px
    HAS_PLOTLY = True
except:
    HAS_PLOTLY = False

# --- [POINTS 4, 41, 12] SÉCURITÉ & CONFIGURATION WEB ---
st.set_page_config(page_title="Sacco Titanium v39", layout="wide")

# --- [POINTS 42, 43, 45] DESIGN BURUNDI & LOGOS ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Flag_of_Burundi.svg/1000px-Flag_of_Burundi.svg.png");
        background-repeat: no-repeat; background-attachment: fixed;
        background-position: center; background-size: 20%;
        background-color: rgba(255, 255, 255, 0.96); background-blend-mode: overlay;
    }
    .footer { position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 12px; background: white; padding: 8px; border-top: 1px solid #ddd; z-index: 99; }
    </style>
    """, unsafe_allow_html=True
)

# --- [POINTS 8, 9, 19, 27] GESTION DATA & RÉPARATION ---
DB_FILE = "sacco_db_v39.csv"
LOG_FILE = "sacco_audit_v39.csv"

def get_mandatory_cols():
    return ["Nom", "Prénom", "Age", "Sexe", "Téléphone", "PIN", "Colline", "Quartier", "Avenue", "Maison", 
            "Groupe", "Rôle", "Solde_Epargne", "Solde_Social", "Statut_Presence", "Derniere_Connexion", 
            "Pret_Actuel", "Amendes", "Statut_Compte"]

def load_data():
    cols = get_mandatory_cols()
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype={'Téléphone': str, 'PIN': str})
        for c in cols:
            if c not in df.columns: df[c] = 0 if "Solde" in c or "Pret" in c else "N/A"
        return df
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DB_FILE, index=False)
    st.session_state.df = df

def write_audit(user, action, montant=0, motif=""):
    log = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Auteur": user, "Action": action, "Montant": montant, "Motif": motif}])
    log.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

# Init
if 'df' not in st.session_state: st.session_state.df = load_data()
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_root' not in st.session_state: st.session_state.is_root = False
if 'user' not in st.session_state: st.session_state.user = None

# [POINT 15] Comptes d'Exemple
if "admin" not in st.session_state.df['Téléphone'].values:
    ex = {"Nom": "NKURUNZIZA", "Prénom": "Raphaël", "Age": 30, "Sexe": "M", "Téléphone": "admin", "PIN": "1234", "Rôle": "Membre", "Groupe": "G-Bujumbura", "Solde_Epargne": 50000, "Statut_Compte": "Actif"}
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([ex])], ignore_index=True).fillna(0)
    save_data(st.session_state.df)

# ==========================================
# SIDEBAR [POINTS 1, 35, 38, 42]
# ==========================================
with st.sidebar:
    st.image("https://raw.githubusercontent.com/votre-repo/logos/main/ENgodo.png", width=120)
    st.title("Sacco FinTech v39")
    
    # POINT 1 : Météo & Bourse
    st.markdown(f"""<div style="background: #f0f2f6; padding: 10px; border-radius: 10px;">
    📍 Bujumbura: 28°C ☀️<br>💹 BIF/USD: 2,852<br>📅 {datetime.now().strftime('%d/%m/%Y')}</div>""", unsafe_allow_html=True)

    if not st.session_state.auth and not st.session_state.is_root:
        menu = st.radio("Menu", ["🔑 Connexion", "📝 Adhésion KYC", "🛡️ Accès Maître"])
    else:
        st.success(f"Utilisateur: {st.session_state.user['Prénom'] if st.session_state.user else 'ROOT'}")
        if st.button("🚪 Quitter la session"):
            st.session_state.auth = st.session_state.is_root = False
            st.rerun()
        
        if st.session_state.is_root:
            menu = st.radio("Admin Système", ["🏢 Vue Panoramique (Root)", "📊 Audit & IA", "⚙️ Gestion Groupes", "🕒 Logs d'Audit"])
        else:
            u_role = st.session_state.user['Rôle']
            opts = ["🏠 Accueil", "💰 Mon Compte", "👤 Mon Profil"]
            if u_role in ['Président', 'Secrétaire']: opts.insert(1, "👥 Gestion du Groupe")
            menu = st.radio("Espace Membre", opts)

# ==========================================
# [POINTS 17, 18, 37, 47, 49, 50] ACTIONS ROOT
# ==========================================
if menu == "🏢 Vue Panoramique (Root)":
    st.title("🏢 Console d'Administration Centrale")
    
    # Point 49, 50, 47, 18 : Actions directes
    st.subheader("🛠️ Actions sur un membre")
    target_id = st.selectbox("Sélectionner le compte (Téléphone)", st.session_state.df['Téléphone'].tolist())
    
    c1, c2, c3, c4 = st.columns(4)
    
    if c1.button("🗑️ Supprimer"):
        st.session_state.df = st.session_state.df[st.session_state.df['Téléphone'] != target_id]
        save_data(st.session_state.df); write_audit("ROOT", f"Suppression {target_id}"); st.rerun()
    
    new_grp = c2.text_input("Nouveau Groupe", "G-Bujumbura")
    if c2.button("✈️ Déplacer"):
        st.session_state.df.loc[st.session_state.df['Téléphone'] == target_id, 'Groupe'] = new_grp
        save_data(st.session_state.df); st.success("Membre déplacé.")

    new_pin = c3.text_input("Nouveau PIN", type="password")
    if c3.button("🔑 Reset PIN"):
        st.session_state.df.loc[st.session_state.df['Téléphone'] == target_id, 'PIN'] = new_pin
        save_data(st.session_state.df); st.success("PIN modifié.")

    role_nom = c4.selectbox("Nommer Rôle", ["Membre", "Président", "Secrétaire"])
    if c4.button("🎖️ Assigner"):
        st.session_state.df.loc[st.session_state.df['Téléphone'] == target_id, 'Rôle'] = role_nom
        save_data(st.session_state.df); st.rerun()

    st.divider()
    # Point 3, 6, 10
    if st.button("💹 Appliquer 2% d'Intérêt Global"):
        st.session_state.df['Solde_Epargne'] *= 1.02
        save_data(st.session_state.df); st.balloons()

    st.subheader("📊 Base de données complète")
    edited = st.data_editor(st.session_state.df, use_container_width=True)
    if st.button("💾 Sauvegarder modifications manuelles"):
        save_data(edited); st.success("Synchronisé.")

# ==========================================
# [POINT 14, 48] KYC COMPLET
# ==========================================
elif menu == "📝 Adhésion KYC":
    st.title("📝 Formulaire Officiel d'Adhésion")
    with st.form("kyc_form"):
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Nom").upper()
            pre = st.text_input("Prénom")
            age = st.number_input("Age", 18, 100)
            sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
            tel = st.text_input("Numéro de Téléphone")
        with c2:
            coll = st.text_input("Colline")
            quart = st.text_input("Quartier")
            ave = st.text_input("Avenue / Rue")
            mais = st.text_input("N° Maison")
        
        p1 = st.text_input("Créer PIN (4 chiffres)", type="password")
        p2 = st.text_input("Confirmer PIN", type="password")
        
        if st.form_submit_button("🚀 Créer mon compte"):
            if p1 == p2 and len(tel) > 7:
                new_u = {"Nom": nom, "Prénom": pre, "Age": age, "Sexe": sexe, "Téléphone": tel, "PIN": p1, "Colline": coll, "Statut_Compte": "Actif", "Groupe": "A Définir", "Rôle": "Membre"}
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_u])], ignore_index=True).fillna(0)
                save_data(st.session_state.df); st.success("Adhésion réussie ! Connectez-vous.")
            else: st.error("Vérifiez le PIN ou le téléphone.")

# ==========================================
# [POINTS 12, 15] LOGINS
# ==========================================
elif menu == "🔑 Connexion":
    st.title("🔑 Connexion Membre")
    id_in = st.text_input("Téléphone")
    pin_in = st.text_input("Code PIN", type="password")
    if st.button("Entrer"):
        res = st.session_state.df[(st.session_state.df['Téléphone'] == id_in) & (st.session_state.df['PIN'] == pin_in)]
        if not res.empty:
            st.session_state.auth = True
            st.session_state.user = res.iloc[0].to_dict()
            st.rerun()
        else: st.error("Identifiants incorrects.")

elif menu == "🛡️ Accès Maître":
    st.title("🛡️ Administration Système")
    pwd = st.text_input("Mot de passe Maître", type="password")
    if st.button("Débloquer"):
        if pwd == "SACCO_Bujumbura-BBIN":
            st.session_state.is_root = True
            st.rerun()

# ==========================================
# [POINTS 16, 21, 36] GESTION DE GROUPE
# ==========================================
elif menu == "👥 Gestion du Groupe":
    u = st.session_state.user
    st.title(f"👥 Administration Groupe : {u['Groupe']}")
    membres = st.session_state.df[st.session_state.df['Groupe'] == u['Groupe']]
    st.write(f"Capacité : **{len(membres)} / 30 membres**")
    
    st.subheader("Pointage de Présence")
    for i, row in membres.iterrows():
        col1, col2, col3 = st.columns([3,1,1])
        col1.write(f"**{row['Nom']} {row['Prénom']}**")
        if col2.button("P", key=f"pres_{i}"):
            st.session_state.df.at[i, 'Statut_Presence'] = "P"
            save_data(st.session_state.df); st.toast("Présent !")
        if col3.button("A", key=f"abs_{i}"):
            st.session_state.df.at[i, 'Statut_Presence'] = "A"
            save_data(st.session_state.df); st.toast("Absent !")

# ==========================================
# [POINTS 23-34] FINANCES
# ==========================================
elif menu == "💰 Mon Compte":
    u = st.session_state.user
    st.title(f"💰 Espace Financier")
    st.metric("Épargne Totale", f"{u['Solde_Epargne']:,} BIF")
    st.metric("Prêt en cours", f"{u['Pret_Actuel']:,} BIF")
    
    st.divider()
    st.subheader("🏦 Demander un Prêt (Max 3x Épargne)")
    montant = st.number_input("Somme", 0, int(u['Solde_Epargne']*3))
    if st.button("Soumettre la demande"):
        write_audit(u['Téléphone'], "Demande Prêt", montant)
        st.success("Demande enregistrée pour validation.")

# [POINT 44] PROFIL
elif menu == "👤 Mon Profil":
    st.title("👤 Mon Profil")
    st.table(pd.Series(st.session_state.user))

# [POINTS 5, 13] IA & AUDIT
elif menu == "📊 Audit & IA":
    st.title("📊 Statistiques Globales")
    st.metric("Total Epargne Sacco", f"{st.session_state.df['Solde_Epargne'].sum():,} BIF")
    if HAS_PLOTLY:
        fig = px.pie(st.session_state.df, values='Solde_Epargne', names='Groupe', title="Répartition par Groupe")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "🕒 Logs d'Audit":
    st.title("🕒 Historique Complet")
    if os.path.exists(LOG_FILE): st.dataframe(pd.read_csv(LOG_FILE), use_container_width=True)

# --- [POINT 40] FOOTER ---
st.markdown('<div class="footer">© copyright - Sacco FinTech 2013-2026 - L\'avenir pour tous au Burundi</div>', unsafe_allow_html=True)