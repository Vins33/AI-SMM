# Percorso file: pages/3_Chat_con_Agente_Graph.py

import asyncio

import nest_asyncio
import streamlit as st

from src.core.agent_graph import get_agent_graph_response

nest_asyncio.apply()
# --- Configurazione Pagina ---
st.set_page_config(page_title="Agente LangGraph", layout="wide")
st.title("🤖 Chat con Agente (LangGraph)")
st.markdown("""
Questa chat è connessa a un agente LangGraph.
L'agente può decidere autonomamente se:
1.  **Cercare sul web** (tramite `web_search_tool`)
2.  **Leggere dalla Knowledge Base** (tramite `read_from_kb_tool`)
3.  **Scrivere nella Knowledge Base** (tramite `write_to_kb_tool`)
""")

# --- Gestione Session State per la Cronologia ---
if "agent_graph_messages" not in st.session_state:
    st.session_state.agent_graph_messages = []

# --- Render della Cronologia Chat ---
for message in st.session_state.agent_graph_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input Utente e Logica di Esecuzione ---
if prompt := st.chat_input("Esempio: 'Cosa è successo oggi a Milano?'"):

    # 1. Aggiungi e mostra il messaggio dell'utente
    user_message = {"role": "user", "content": prompt}
    st.session_state.agent_graph_messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Ottieni la risposta dall'Agente (Grafo)
    with st.chat_message("assistant"):
        with st.spinner("L'Agente LangGraph sta elaborando... (Controlla il terminale per i log dei tool)"):

            # Prendiamo la cronologia attuale (escluso l'ultimo input utente)
            history_for_agent = st.session_state.agent_graph_messages[:-1]

            try:
                # Esegui la funzione asincrona del grafo
                # asyncio.run() è necessario per chiamare codice async da Streamlit (che è sync)
                final_response_message = asyncio.run(get_agent_graph_response(prompt, history_for_agent))

                # 'final_response_message' è un oggetto AIMessage di LangChain
                response_text = final_response_message.content

                st.markdown(response_text)

                # 3. Salva la risposta completa dell'assistente (inclusi i tool_calls, anche se vuoti)
                # Questo è fondamentale affinché la history sia corretta per il prossimo turno.
                st.session_state.agent_graph_messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": final_response_message.tool_calls
                })

            except Exception as e:
                error_msg = f"Si è verificato un errore critico nel grafo: {str(e)}"
                st.error(error_msg)
                st.session_state.agent_graph_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "tool_calls": []
                })
