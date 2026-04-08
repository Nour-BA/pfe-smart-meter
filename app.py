import streamlit as st
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="PFE Smart Meter Dashboard", layout="wide")
st.title("⚡ Système de Monitoring Énergétique (PFE)")

# --- INITIALISATION DES VARIABLES DE SESSION ---
# Pour éviter que Streamlit ne réinitialise tout à chaque clic
if 'msg_history' not in st.session_state:
    st.session_state.msg_history = []
if 'last_data' not in st.session_state:
    st.session_state.last_data = {"v": 0, "i": 0, "p": 0}
if 'status' not in st.session_state:
    st.session_state.status = "Initialisation..."

# --- CONNEXION MONGODB ---
@st.cache_resource
def get_mongodb():
    try:
        client = MongoClient(st.secrets["MONGO_URI"])
        db = client["PFE_SmartCity"]
        # On teste la connexion
        client.admin.command('ping')
        return db["energy_data"]
    except Exception as e:
        st.error(f"Erreur MongoDB : {e}")
        return None

collection = get_mongodb()

# --- LOGIQUE MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.status = "✅ Connecté à HiveMQ"
        # On s'abonne au topic exact
        client.subscribe("maison/compteur")
    else:
        st.session_state.status = f"❌ Erreur de connexion (code {rc})"

def on_message(client, userdata, msg):
    try:
        # 1. Décoder le message
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        # 2. Ajouter un timestamp
        data["timestamp"] = datetime.now()
        
        # 3. Mettre à jour l'interface (Session State)
        st.session_state.last_data = data
        st.session_state.msg_history.insert(0, data) # Ajoute au début de la liste
        
        # 4. Sauvegarder dans MongoDB Atlas
        if collection is not None:
            collection.insert_one(data)
            
    except Exception as e:
        print(f"Erreur lors de la réception : {e}")

# --- DÉMARRAGE DU CLIENT MQTT ---
if 'mqtt_client' not in st.session_state:
    try:
        client = mqtt.Client(transport="tcp")
        client.username_pw_set(st.secrets["MQTT_USER"], st.secrets["MQTT_PASS"])
        client.tls_set() # Obligatoire pour HiveMQ Cloud
        
        client.on_connect = on_connect
        client.on_message = on_message
        
        client.connect(st.secrets["MQTT_BROKER"], 8883)
        client.loop_start()
        st.session_state.mqtt_client = client
    except Exception as e:
        st.error(f"Erreur Client MQTT : {e}")

# --- AFFICHAGE DASHBOARD ---
st.subheader(f"Statut : {st.session_state.status}")

# Colonnes pour les Metrics
col1, col2, col3 = st.columns(3)
d = st.session_state.last_data
col1.metric("Tension", f"{d.get('v')} V")
col2.metric("Courant", f"{d.get('i')} A")
col3.metric("Puissance", f"{d.get('p')} W")

st.divider()

# --- HISTORIQUE ---
st.subheader("📊 Historique des données")

tab1, tab2 = st.tabs(["Flux en direct (Session)", "Archive (MongoDB)"])

with tab1:
    if st.session_state.msg_history:
        st.table(st.session_state.msg_history[:5]) # Affiche les 5 derniers
    else:
        st.info("En attente de messages depuis HiveMQ...")

with tab2:
    if st.button("Charger depuis MongoDB Atlas"):
        if collection is not None:
            docs = list(collection.find().sort("timestamp", -1).limit(10))
            if docs:
                st.write(docs)
            else:
                st.warning("La base de données est vide.")
