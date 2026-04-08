import streamlit as st
from pymongo import MongoClient
import pandas as pd

st.title("📈 Dashboard de Contrôle - Smart Meter")

# Connexion MongoDB
client_db = MongoClient("ton_lien_atlas")
db = client_db["SmartMeter_PFE"]
collection = db["historique_energie"]

st.subheader("Dernières données enregistrées")

# Bouton pour rafraîchir
if st.button('Actualiser les données'):
    # Récupérer les 10 derniers messages
    data = list(collection.find().sort("timestamp", -1).limit(10))
    if data:
        df = pd.DataFrame(data).drop(columns=['_id']) # On enlève l'ID technique de Mongo
        st.table(df)
    else:
        st.write("Aucune donnée trouvée dans SmartMeter_PFE -> historique_energie")
