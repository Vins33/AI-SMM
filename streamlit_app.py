import streamlit as st

# Configurazione della pagina principale
st.set_page_config(page_title="Generatore Contenuti AI", page_icon="🤖", layout="wide")

st.title("🤖 Benvenuto nel Generatore di Contenuti AI")

st.sidebar.success("Seleziona una pagina qui sopra per iniziare.")

st.markdown(
    """
    Questa applicazione è progettata per aiutarti a creare contenuti per Instagram in modo efficiente.

    **Ecco come funziona:**

    1. **Vai alla pagina `1_Carica_e_Classifica`:**
       - Carica un file CSV contenente le domande o gli spunti che vuoi trasformare in post.
       - L'AI analizzerà e classificherà ogni domanda, salvandola nel database.

    2. **Vai alla pagina `2_Genera_Contenuto`:**
       - Visualizza tutte le domande classificate.
       - Seleziona una domanda per generare un post completo per Instagram, arricchito con informazioni pertinenti.

    Usa il menu a sinistra per navigare tra le pagine e iniziare.
    """
)
