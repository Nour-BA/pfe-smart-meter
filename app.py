import streamlit as st
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Smart Meter PFE", layout="wide")
st.title("⚡ Dashboard Énergétique : Le Pont de Données")

# --- 2. RÉCUPÉRATION DES SECRETS (ST.SECRETS) ---
# Ces valeurs seront configurées dans le menu "Settings > Secrets" de Streamlit Cloud
try:
    MONGO_URI = st.secrets["MONGO_URI"]
    MQTT_BROKER = st.secrets["MQTT_BROKER"]
    MQTT_USER = st.secrets["MQTT_USER"]
    MQTT_PASS = st.secrets["MQTT_PASS"]
except Exception as e:
    st.error("⚠️ Les Secrets ne sont pas encore configurés ! Allez dans Settings > Secrets.")
    st.stop()

MQTT_TOPIC = "maison/compteur"

# --- 3. CONNEXION MONGODB ---
@st.cache_resource
def get_database():
    client = MongoClient(MONGO_URI)
    # Nom de la base : SmartMeter_PFE | Nom de la collection : mesures
    db = client["SmartMeter_PFE"]
    return db["mesures"]

db_collection = get_database()

# --- 4. LOGIQUE DU PONT (MQTT -> MONGODB) ---
def on_message(client, userdata, msg):
    try:
        # On décode le message JSON envoyé par le compteur (ESP32 ou simulateur)
        payload = json.loads(msg.payload.decode())
        
        # On ajoute la date et l'heure précise de réception
        payload["timestamp"] = datetime.now()
        
        # --- ACTION DU PONT : INSERTION DANS LA BASE DE DONNÉES ---
        db_collection.insert_one(payload)
        print("Donnée enregistrée avec succès !")
        
    except Exception as e:
        print(f"Erreur lors du traitement du message : {e}")

# Configuration du client MQTT
# Utilisation de la version 1 du callback pour la compatibilité HiveMQ
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set() # Obligatoire pour HiveMQ Cloud (SSL)
mqtt_client.on_message = on_message

# --- 5. INTERFACE ET BOUTONS ---
col1, col2 = st.columns(2)

with col1:
    st.info("📡 **Connexion au Broker**")
    if st.button("🚀 ACTIVER LE PONT", use_container_width=True):
        try:
            mqtt_client.connect(MQTT_BROKER, 8883)
            mqtt_client.subscribe(MQTT_TOPIC)
            mqtt_client.loop_start() # Lance l'écoute en arrière-plan
            st.success("✅ Le pont est actif ! Il écoute et enregistre les données.")
        except Exception as e:
            st.error(f"Échec de connexion : {e}")

with col2:
    st.info("📊 **Affichage**")
    if st.button("🔄 ACTUALISER LES DONNÉES", use_container_width=True):
        st.rerun()

st.divider()

# --- 6. VISUALISATION DES DONNÉES DEPUIS MONGODB ---
st.subheader("📋 Dernières mesures extraites de la base de données")

# On récupère les 10 dernières entrées triées par date
cursor = db_collection.find().sort("timestamp", -1).limit(10)
data_list = list(cursor)

if data_list:
    # Nettoyage de l'ID MongoDB pour l'affichage tableau
    for doc in data_list:
        doc.pop('_id', None)
        if "timestamp" in doc:
            doc["timestamp"] = doc["timestamp"].strftime("%H:%M:%S")

    # Affichage du tableau
    st.dataframe(data_list, use_container_width=True)

    # Graphique de puissance (clé 'p' dans ton JSON)
    puissances = [float(d.get('p', 0)) for d in reversed(data_list)]
    st.line_chart(puissances)
else:
    st.warning("Base de données vide. Activez le pont et envoyez une donnée sur HiveMQ.")
