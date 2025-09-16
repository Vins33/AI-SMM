import httpx
import streamlit as st

# --- CONFIGURAZIONE ---
BACKEND_URL = "http://app:8000/api"
st.set_page_config(page_title="Carica e Classifica", layout="wide")


# --- FUNZIONI DI UTILITÀ ---
def display_error(e: httpx.HTTPError):
    """Mostra un messaggio di errore dettagliato all'utente."""
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json().get("detail", "Si è verificato un errore interno del server.")
            st.error(f"Errore dal server ({e.response.status_code}): {detail}")
        except Exception:
            st.error(f"Errore dal server ({e.response.status_code}): {e.response.text}")
    else:
        st.error(f"Errore di connessione al backend: Assicurati che sia in esecuzione. Dettagli: {e}")


# Inizializza lo stato della sessione per i messaggi di successo
if "success_message" not in st.session_state:
    st.session_state.success_message = None

# --- INTERFACCIA UTENTE ---
st.title("1. Carica e Classifica le Domande")

if st.session_state.success_message:
    st.success(st.session_state.success_message, icon="✅")
    st.session_state.success_message = None

st.markdown(
    "Carica qui il tuo file CSV. L'applicazione classificherà ogni riga e la salverà,"
    " preparandola per la generazione di contenuti."
)

with st.form("upload_form", clear_on_submit=True):
    uploaded_file = st.file_uploader("Scegli un file CSV con le colonne 'Title' e 'Body'", type="csv")
    # CORRETTO: Sostituito il parametro deprecato 'use_container_width'
    submitted = st.form_submit_button(
        "🚀 Avvia Classificazione",
        type="primary",
        use_container_width=True,  # Lasciamo questo perché è ancora valido per form_submit_button
    )

    if submitted and uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        with st.spinner("Classificazione in corso... Questo potrebbe richiedere alcuni minuti."):
            try:
                response = httpx.post(f"{BACKEND_URL}/process-csv/", files=files, timeout=600)
                response.raise_for_status()
                result = response.json().get("details", {})

                st.session_state.success_message = (
                    f"Classificazione completata! {result.get('processed_count', 0)} domande processate."
                )

                st.cache_data.clear()
                st.rerun()
            except httpx.HTTPError as e:
                display_error(e)

st.info(
    "Dopo aver caricato il file, vai alla pagina 'Genera Contenuto' per vedere i risultati e creare i post.", icon="👉"
)
