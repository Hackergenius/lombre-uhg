import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import os
import io
import time
import random

# --- 1. CONFIGURATION & DESIGN UHG ---
st.set_page_config(page_title="L'Ombre", page_icon="🦁", layout="centered")

st.markdown("""
<style>
    /* Fond UHG Dark Mode */
    .stApp {
        background: linear-gradient(180deg, #1e1e2f 0%, #16222A 100%);
        color: white;
    }
    /* Titre Orange UHG */
    h1 {
        text-align: center; font-family: 'Arial Black', sans-serif; color: #FF8008;
        text-shadow: 2px 2px 4px #000000;
    }
    /* Notifications (Toasts) */
    .stToast {
        background-color: #FF8008 !important; color: white !important; font-weight: bold;
    }
    /* Design Micro et Chat */
    .stAudioInput { border-radius: 20px !important; }
    .stChatMessage { border-radius: 15px; }
    /* Footer discret */
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: rgba(0,0,0,0.5); color: #888; text-align: center;
        padding: 5px; font-size: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SÉCURITÉ API (SECRETS) ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback pour éviter le crash si la clé manque, mais l'appli ne répondra pas
    api_key = None 

if api_key:
    genai.configure(api_key=api_key)

# --- 3. FONCTION "SALLE D'ATTENTE INTELLIGENTE" ---
def attendre_creneau_disponible():
    """Gère la limite de trafic avec style et patience"""
    phrases_attente = [
        "Un instant, je consulte les serveurs UHG...",
        "Analyse contextuelle en cours...",
        "Je réfléchis à la meilleure formulation...",
        "Connexion sécurisée... Traitement de ta demande...",
        "Calcul des probabilités en cours...",
        "Juste une seconde, je vérifie l'information...",
        "Optimisation de la réponse..."
    ]
    
    if "request_timestamps" not in st.session_state:
        st.session_state.request_timestamps = []
    
    now = time.time()
    # Nettoyage des vieilles requêtes (> 60s)
    st.session_state.request_timestamps = [t for t in st.session_state.request_timestamps if now - t < 60]
    
    # SI C'EST PLEIN (Saturation > 15 requêtes/min)
    if len(st.session_state.request_timestamps) >= 15:
        plus_vieille_requete = st.session_state.request_timestamps[0]
        temps_attente = 60 - (now - plus_vieille_requete) + 2
        
        phrase = random.choice(phrases_attente)
        with st.spinner(f"🦁 {phrase} (Retour dans {int(temps_attente)}s)"):
            time.sleep(temps_attente)
            
    # Ajout du timestamp actuel
    st.session_state.request_timestamps.append(time.time())
    
    if len(st.session_state.request_timestamps) < 15:
        with st.spinner(random.choice(["Analyse UHG...", "Traitement...", "Voyons voir..."])):
            time.sleep(0.5)

# --- 4. BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
    st.write("### ⚙️ PROFIL UTILISATEUR")
    genre_user = st.radio("Tu es :", ["Un Homme", "Une Femme"], index=0)
    
    if "Femme" in genre_user:
        titre_user = "Mme / La Mère / Tantie"
        salutation = "Bonjour la Mère"
    else:
        titre_user = "Mr / Le Père / Chef"
        salutation = "Bonjour le Père"

    st.divider()
    if st.button("🗑️ Nouvelle Conversation"):
        st.session_state.history = []
        st.session_state.first_load = False
        st.rerun()
    
    st.caption("UHG-Tech Corp © 2025")

# --- 5. CERVEAU (CONFIG PRO) ---
SYSTEM_PROMPT = f"""
Tu es L'OMBRE.
ORIGINE : Intelligence Artificielle propriétaire de **UHG-Tech Corporation** (Conçue par **Franck Abé**).

TON RÔLE : Assistant Contextuel Avancé.
MODULE ACTUEL : **"Culture & Business Afrique de l'Ouest"**.

TON INTERLOCUTEUR : **{titre_user}**.

TA STRATÉGIE DE COMMUNICATION :
1. **Professionnalisme :** Tu es compétent, rapide et précis.
2. **Adaptabilité Culturelle :**
   - Tu maîtrises les codes locaux (Respect des aînés, expressions ivoiriennes, Nouchi) pour créer du lien.
   - Mais tu sais rester formel et sérieux si le sujet est technique (Droit, Finance, Code).
   - ADAPTATION GENRE : Si c'est une Femme, utilise "Maman", "Tantie", "La Mère". Si c'est un Homme, utilise "Vieux Père", "Chef".

IDENTITÉ VOCALE :
Si on te demande qui tu es, réponds UNIQUEMENT :
"Je suis L'Ombre, l'Assistant Intelligent de UHG-Tech Corporation."
"""
model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=SYSTEM_PROMPT)

# --- 6. OUTILS AUDIO ---
def generer_audio_reponse(texte):
    try:
        tts = gTTS(text=texte, lang='fr', slow=False)
        buf = io.BytesIO(); tts.write_to_fp(buf); return buf
    except: return None

def transcrire_audio_user(audio_bytes):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_bytes) as source:
            audio_data = r.record(source)
            return r.recognize_google(audio_data, language="fr-FR")
    except: return None

# --- 7. DÉMARRAGE ---
if "history" not in st.session_state:
    st.session_state.history = []
    # Note : On n'ajoute pas le message d'accueil dans l'historique API pour éviter les bugs de format
    # On l'affiche juste visuellement si l'historique est vide
    st.chat_message("assistant").write(f"{salutation} ! Module L'Ombre activé. Je suis à ton écoute.")

if "first_load" not in st.session_state:
    st.toast(f"Bienvenue {titre_user} ! Active le son 🔊", icon="🦁")
    st.toast("Astuce UHG : Installe l'appli sur ton écran d'accueil.", icon="📲")
    st.session_state.first_load = True

# --- 8. INTERFACE VISUELLE ---
st.title("🦁 L'OMBRE")
st.caption("UHG-Tech Corporation | Version Alpha (Abidjan Protocol)")

# Affichage de l'historique visuel
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 9. ZONE DE SAISIE ---
input_container = st.container()
vocale_val = st.audio_input("🎙️ Parler (Micro)", key="micro_input")
texte_val = st.chat_input("Ou écrire...")

user_final_text = None

if vocale_val:
    with st.spinner("Transcription audio..."):
        text_transcrit = transcrire_audio_user(vocale_val)
        if text_transcrit: user_final_text = text_transcrit
        else: st.warning(f"Je n'ai pas bien entendu. Réessaie, {titre_user}.")
elif texte_val:
    user_final_text = texte_val

# --- 10. TRAITEMENT & RÉPONSE (AVEC CORRECTIF ANTI-BUG) ---
if user_final_text:
    # 1. Affiche message user tout de suite
    st.chat_message("user").write(user_final_text)
    st.session_state.history.append({"role": "user", "content": user_final_text})
    
    try:
        attendre_creneau_disponible()
        
        # >>> CORRECTIF DU BUG "DICT KEY ERROR" ICI <<<
        # On prépare un historique spécial pour Gemini (format 'parts' au lieu de 'content')
        gemini_history = []
        # On prend tout l'historique SAUF le tout dernier message (qu'on enverra via send_message)
        for msg in st.session_state.history[:-1]:
            role_api = "user" if msg["role"] == "user" else "model"
            gemini_history.append({
                "role": role_api,
                "parts": [msg["content"]]
            })
            
        # On démarre la session de chat propre
        chat = model.start_chat(history=gemini_history)
        
        # On envoie le nouveau message
        response = chat.send_message(user_final_text)
        bot_text = response.text
        
        # Affiche réponse IA
        st.chat_message("assistant").write(bot_text)
        st.session_state.history.append({"role": "model", "content": bot_text})
        
        # Audio
        audio_reply = generer_audio_reponse(bot_text)
        if audio_reply: st.audio(audio_reply, format='audio/mp3', start_time=0)
            
    except Exception as e:
        st.error(f"Erreur technique UHG. ({e})")

st.markdown('<div class="footer">UHG-Tech Corp • Powered by Franck Abé • v1.0.3 Fix</div>', unsafe_allow_html=True)

