# pages/Explainability.py
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Explainability Dashboard", page_icon="🧠", layout="wide")
st.title("🧠 Explainability Dashboard – AI-SMM")
st.markdown("""
Monitoraggio e spiegabilità delle generazioni LLM eseguite da Ollama.
""")

LOG_PATH = Path("src/data/audit_logs.json")
if not LOG_PATH.exists():
    st.warning("Nessun log trovato. Genera almeno una risposta tramite Ollama.")
    st.stop()

with open(LOG_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])

st.metric("Totale interazioni", len(df))
st.metric("Latenza media (s)", round(df["latency"].mean(), 2))
st.metric("Token medi per risposta", round(df["tokens"].mean(), 1))

fig_latency = px.line(df, x="timestamp", y="latency", title="Andamento Latenza")
fig_tokens = px.histogram(df, x="tokens", title="Distribuzione Tokens")

st.plotly_chart(fig_latency, use_container_width=True)
st.plotly_chart(fig_tokens, use_container_width=True)

selected = st.selectbox("Analizza una sessione:", df["session_id"])
record = df[df["session_id"] == selected].iloc[0]
st.write("**Prompt:**", record["prompt"])
st.write("**Risposta:**", record["response"])
st.info(f"**Spiegazione:** {record['explanation']}")
