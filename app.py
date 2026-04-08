import streamlit as st
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="PFE Smart Meter Dashboard", layout="wide")

# --- CONNEXION MONGODB ---
@st.cache_resource
def init_mongodb():
    # Récupération de l'URI depuis les secrets de Streamlit Cloud
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client["PFE_SmartCity"]
    return db["energy_data"]

collection = init_mongodb()

# --- LOGIQUE MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.status = "✅ Connecté à HiveMQ"
        client.subscribe("maison/compteur")
    else:
        st.session_state.status = f"❌ Erreur de connexion (code {rc})"

def on_message(client, userdata, msg):
    try:
        # Décodage du JSON envoyé par l'ESP32
        data = json.loads(msg.payload.decode())
        # Ajout d'un timestamp pour l'historique
        data["timestamp"] = datetime.now()
        
        # Insertion dans MongoDB Atlas
        collection.insert_one(data)
        
        # Mise à jour de l'affichage en temps réel
        st.session_state.last_data = data
    except Exception as e:
        print(f"Erreur traitement message: {e}")

# --- INITIALISATION DU CLIENT MQTT ---
if 'mqtt_client' not in st.session_state:
    client = mqtt.Client()
    # Utilisation des secrets pour HiveMQ
    client.username_pw_set(st.secrets["MQTT_USER"], st.secrets["MQTT_PASS"])
    client.tls_set() # Sécurité obligatoire pour HiveMQ Cloud
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(st.secrets["MQTT_BROKER"], 8883)
        client.loop_start()
        st.session_state.mqtt_client = client
    except Exception as e:
        st.error(f"Impossible de se connecter au Broker: {e}")

# --- INTERFACE STREAMLIT ---
st.title("⚡ Système de Monitoring Énergétique (PFE)")
st.write(f"Statut du serveur : **{st.session_state.get('status', 'Initialisation...')}**")

col1, col2, col3 = st.columns(3)

# Affichage des dernières valeurs reçues
if 'last_data' in st.session_state:
    d = st.session_state.last_data
    col1.metric("Tension (V)", f"{d.get('v', 0)} V")
    col2.metric("Courant (A)", f"{d.get('i', 0)} A")
    col3.metric("Puissance (W)", f"{d.get('p', 0)} W")
else:
    st.info("En attente des premières données de l'ESP32...")

st.divider()

# --- PARTIE ANALYSE ---
st.subheader("📊 Historique récent (MongoDB)")
if st.button("Actualiser les données"):
    # Récupère les 10 dernières entrées de MongoDB
    cursor = collection.find().sort("timestamp", -1).limit(10)
    data_list = list(cursor)
    if data_list:
        st.table(data_list)
    else:
        st.warning("Aucune donnée trouvée dans la base.")

st.sidebar.write("### Paramètres")
st.sidebar.info("Le pont tourne en arrière-plan. Les données de l'ESP32 sont automatiquement envoyées vers MongoDB Atlas.")
