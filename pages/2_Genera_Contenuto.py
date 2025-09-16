import httpx
import pandas as pd
import streamlit as st

# --- CONFIGURAZIONE ---
BACKEND_URL = "http://app:8000/api"
st.set_page_config(page_title="Genera Contenuto", layout="wide")


# --- FUNZIONI DI UTILITÀ ---
@st.cache_data(ttl=300)  # Cache per 5 minuti
def load_questions_from_backend():
    """Carica tutte le domande dal backend e le restituisce come dizionario."""
    try:
        response = httpx.get(f"{BACKEND_URL}/questions/")
        response.raise_for_status()
        questions_list = response.json()
        return {q["id"]: q for q in questions_list}
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        display_error(e)
        return {}


def get_display_dataframe(questions_dict):
    """Prepara il DataFrame per la visualizzazione."""
    if not questions_dict:
        return pd.DataFrame(columns=["id", "Testo Domanda (preview)", "Classificazione", "Contenuto Generato"])
    data_for_df = [
        {
            "id": q_id,
            "Testo Domanda (preview)": q_data["question_text"][:100] + "..."
            if len(q_data["question_text"]) > 100
            else q_data["question_text"],
            "Classificazione": q_data["classification"],
            "Contenuto Generato": "✅" if q_data["generated_content"] else "❌",
        }
        for q_id, q_data in questions_dict.items()
    ]
    sorted_data = sorted(data_for_df, key=lambda x: x["id"], reverse=True)
    return pd.DataFrame(sorted_data)


def display_error(e: httpx.HTTPError):
    """Mostra un messaggio di errore dettagliato."""
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detail = e.response.json().get("detail", "Si è verificato un errore interno del server.")
            st.error(f"Errore dal server ({e.response.status_code}): {detail}")
        except Exception:
            st.error(f"Errore dal server ({e.response.status_code}): {e.response.text}")
    else:
        st.error(f"Errore di connessione al backend: Assicurati che sia in esecuzione. Dettagli: {e}")


# --- INTERFACCIA UTENTE ---
st.title("2. Seleziona una Domanda e Genera il Contenuto")

# Inizializzazione dello stato
if "selected_question_id" not in st.session_state:
    st.session_state.selected_question_id = None
if "success_message" not in st.session_state:
    st.session_state.success_message = None

if st.session_state.success_message:
    st.success(st.session_state.success_message, icon="✅")
    st.session_state.success_message = None

all_questions_dict = load_questions_from_backend()

# Pulsante di aggiornamento manuale
_, col2 = st.columns([3, 1])
if col2.button("🔄 Aggiorna Lista", use_container_width=True):
    st.cache_data.clear()
    st.session_state.selected_question_id = None
    st.rerun()

if not all_questions_dict:
    st.warning("Nessuna domanda trovata. Vai alla pagina 'Carica e Classifica' per iniziare.")
else:
    df_questions = get_display_dataframe(all_questions_dict)
    st.info("Clicca su una riga per selezionare una domanda e vedere le azioni disponibili.")

    # Visualizzazione della tabella
    event = st.dataframe(
        df_questions,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if event.selection.rows:
        selected_index = event.selection.rows[0]
        st.session_state.selected_question_id = int(df_questions.iloc[selected_index]["id"])

    # Sezione delle azioni per la riga selezionata
    selected_id = st.session_state.selected_question_id
    if selected_id and selected_id in all_questions_dict:
        selected_question_data = all_questions_dict.get(selected_id)
        st.subheader(f"Azioni per la Domanda ID: {selected_id}")

        with st.expander("👁️ Visualizza Testo Completo della Domanda", expanded=True):
            st.text_area(
                "Testo completo:",
                selected_question_data["question_text"],
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )

        action_cols = st.columns([1, 1, 3])

        generate_button_disabled = bool(selected_question_data["generated_content"])
        if action_cols[0].button(
            "✨ Genera Contenuto", type="primary", use_container_width=True, disabled=generate_button_disabled
        ):
            with st.spinner("Generazione del contenuto in corso..."):
                try:
                    response = httpx.post(f"{BACKEND_URL}/generate-content/{selected_id}", timeout=600)
                    response.raise_for_status()
                    st.session_state.success_message = "Contenuto generato e salvato!"
                    st.cache_data.clear()
                    st.rerun()
                except httpx.HTTPError as e:
                    display_error(e)

        reset_button_disabled = not bool(selected_question_data["generated_content"])
        if action_cols[1].button("🔄 Resetta Contenuto", use_container_width=True, disabled=reset_button_disabled):
            with st.spinner("Reset del contenuto in corso..."):
                try:
                    response = httpx.post(f"{BACKEND_URL}/questions/{selected_id}/reset-content")
                    response.raise_for_status()
                    st.session_state.success_message = f"Contenuto per la domanda {selected_id} resettato!"
                    st.cache_data.clear()
                    st.rerun()
                except httpx.HTTPError as e:
                    display_error(e)

        if selected_question_data["generated_content"]:
            st.divider()
            st.subheader("✅ Contenuto Attualmente Salvato:")
            st.markdown(selected_question_data["generated_content"])
