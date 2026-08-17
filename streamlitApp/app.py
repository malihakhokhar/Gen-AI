import streamlit as st
import requests
import os
from groq import Groq
from dotenv import load_dotenv
import subprocess
import json

load_dotenv()

# -------------------------
# Initialize Groq Client
# -------------------------
groq_client = Groq(api_key=os.getenv("GROQ_KEY"))


# -------------------------
# Helper Function: Get Ollama Models
# -------------------------
def get_installed_ollama_models():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split("\n")

        if len(lines) <= 1:
            return []

        models = []
        for line in lines[1:]:
            model_name = line.split()[0]
            models.append(model_name)

        return models
    except:
        return []


# -------------------------
# Helper Function: Call Ollama Model
# -------------------------
def call_ollama(prompt, model_name):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model_name, "prompt": prompt}

    try:
        response = requests.post(url, json=payload, stream=True)
        output = ""

        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8").replace("data: ", "")
                try:
                    chunk = json.loads(decoded)
                    output += chunk.get("response", "")
                except:
                    pass

        return output
    except Exception as e:
        return f"❌ Error: {e}"


# -------------------------
# Helper Function: Call Groq Model
# -------------------------
def call_groq(prompt):
    chat_completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message.content


# -------------------------
# Streamlit UI Setup
# -------------------------
st.set_page_config(page_title="Local LLM Chat", layout="wide")
st.title("💬 Local & Cloud LLM Chat (Ollama + Groq)")


# -------------------------
# Conversation State
# -------------------------
if "history" not in st.session_state:
    st.session_state.history = []


# -------------------------
# Sidebar
# -------------------------
st.sidebar.header("⚙ Settings")

model_source = st.sidebar.radio("Choose Model Source:", ["Ollama (Local)", "Groq (Cloud)"])

ollama_models = get_installed_ollama_models()

if model_source == "Ollama (Local)":
    if ollama_models:
        selected_model = st.sidebar.selectbox("Choose Local Model:", ollama_models)
    else:
        st.sidebar.warning("⚠ No Ollama models found.\nInstall one using:\n`ollama pull llama3`")
        selected_model = None

# Reset Button
if st.sidebar.button("Reset Conversation"):
    st.session_state.history = []
    st.success("Chat cleared!")


# -------------------------
# Conversation History Panel
# -------------------------
st.sidebar.subheader("📜 Conversation History")

history_box = st.sidebar.container(height=300, border=True)

with history_box:
    if st.session_state.history:
        for role, message in st.session_state.history:
            if role == "user":
                st.markdown(f"🧍 **You:** {message}")
            else:
                st.markdown(f"🤖 **Bot:** {message}")
    else:
        st.write("No messages yet.")


# -------------------------
# Main Chat Input
# -------------------------
user_input = st.text_input("Ask something...")

if user_input:
    # Save user message
    st.session_state.history.append(("user", user_input))

    if model_source == "Ollama (Local)":
        if not selected_model:
            bot_reply = "❌ No model selected. Please install a model."
        else:
            bot_reply = call_ollama(user_input, selected_model)
    else:
        bot_reply = call_groq(user_input)

    st.session_state.history.append(("bot", bot_reply))


# -------------------------
# Display Conversation (Main)
# -------------------------
st.subheader("💬 Chat Output")

for role, message in st.session_state.history:
    if role == "user":
        st.markdown(f"🧍 **You:** {message}")
    else:
        st.markdown(f"🤖 **Bot:** {message}")
