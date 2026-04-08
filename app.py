import streamlit as st
import paho.mqtt.client as mqtt
from pymongo import MongoClient
import os

st.title("🛠 Debug du Pont IoT")

# 1. Test des Secrets
try:
    broker = st.secrets["MQTT_BROKER"]
    st.success(f"✅ Secret trouvé : {broker}")
except:
    st.error("❌ Erreur : Le secret MQTT_BROKER est introuvable dans Streamlit.")

# 2. Test MongoDB
try:
    client_db = MongoClient(st.secrets["MONGO_URI"])
    client_db.admin.command('ping')
    st.success("✅ Connexion MongoDB Atlas réussie !")
except Exception as e:
    st.error(f"❌ Erreur MongoDB : {e}")

# 3. Fonction de réception
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.write("🚀 Connecté au Broker HiveMQ !")
        client.subscribe("maison/compteur")
    else:
        st.write(f"Refus de connexion, code : {rc}")

# Initialisation MQTT
if st.button('Démarrer le test MQTT'):
    client = mqtt.Client()
    client.username_pw_set(st.secrets["MQTT_USER"], st.secrets["MQTT_PASS"])
    client.tls_set() # SÉCURITÉ OBLIGATOIRE
    client.on_connect = on_connect
    try:
        client.connect(st.secrets["MQTT_BROKER"], 8883)
        client.loop_start()
        st.info("Test lancé... Regarde si un message 'Connecté' apparaît.")
    except Exception as e:
        st.error(f"Erreur de connexion HiveMQ : {e}")
