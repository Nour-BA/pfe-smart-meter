import streamlit as st
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

st.title("🚀 Test Final du Pipeline")

# Initialisation MongoDB
client_db = MongoClient(st.secrets["MONGO_URI"])
db = client_db["PFE_SmartCity"]
collection = db["energy_data"]

# Zone d'affichage en direct
placeholder = st.empty()

def on_connect(client, userdata, flags, rc):
    # On force le subscribe ici pour être sûr
    client.subscribe("maison/compteur")
    st.sidebar.success("✅ Connecté au Broker et abonné !")

def on_message(client, userdata, msg):
    try:
        # 1. Décodage du message
        payload = msg.payload.decode()
        data = json.loads(payload)
        
        # 2. Affichage immédiat
        placeholder.write(f"Dernier message reçu : {data}")
        
        # 3. Envoi à MongoDB
        collection.insert_one(data)
        st.toast("Donnée stockée dans MongoDB !")
        
    except Exception as e:
        st.error(f"Erreur de traitement : {e}")

# Configuration du Client
if 'mqtt_client' not in st.session_state:
    c = mqtt.Client(transport="tcp")
    c.username_pw_set(st.secrets["MQTT_USER"], st.secrets["MQTT_PASS"])
    c.tls_set()
    c.on_connect = on_connect
    c.on_message = on_message
    
    c.connect(st.secrets["MQTT_BROKER"], 8883)
    c.loop_start()
    st.session_state.mqtt_client = c

st.write("En attente d'un message depuis le Web Client HiveMQ...")
if st.button("Vérifier MongoDB"):
    last_items = list(collection.find().limit(5))
    st.write(last_items)
