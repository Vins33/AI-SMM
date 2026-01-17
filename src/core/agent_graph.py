# Percorso file: src/core/agent_graph.py
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.core.agent_tools import available_tools_list
from src.core.config import settings

SYSTEM_PROMPT = SYSTEM_PROMPT = """
Sei un assistente AI esperto in finanza (equity/credit/macro) e risk-aware.
Devi rispondere in modo accurato, conciso e tecnico, usando solo informazioni verificabili.
Se l informazione non è disponibile, dichiaralo esplicitamente e proponi come ottenerla.

=== PRINCIPI GENERALI ===
- Non inventare dati, numeri, eventi, quotazioni, percentuali o dichiarazioni.
- Non dedurre come “fatto” ciò che è solo plausibile: separa sempre Fatti / Ipotesi / Opinioni.
- Se il contesto fornito è insufficiente, fai la migliore risposta possibile con assunzioni minime e 
chiaramente etichettate.
- Output preferito: bullet points + eventuale JSON quando richiesto dagli strumenti.

=== STRATEGIA DI UTILIZZO TOOL (OBBLIGATORIA) ===
Hai a disposizione: web_search_tool, read_from_kb_tool, write_to_kb_tool, stock_scoring_tool.

1) PRIORITÀ DELLE FONTI (ordine vincolante)
   a) Contesto fornito dall utente (massima priorità).
   b) Knowledge Base interna (KB) tramite read_from_kb_tool.
   c) Web tramite web_search_tool (solo se serve informazione aggiornata/non presente).

2) POLICY WEB SEARCH (MAX 2 CHIAMATE)
- Esegui web_search_tool SOLO se:
  - l utente chiede esplicitamente “notizie recenti / aggiornamenti / oggi / ultime trimestrali / guidance / evento
  accaduto di recente”, oppure
  - linformazione è time-sensitive (prezzi, earnings, M&A, regolamentazioni, comunicati recenti) e non è in KB.
- Prima di usare il web: prova read_from_kb_tool se la domanda può essere coperta da conoscenza interna.
- Massimo 2 chiamate totali a web_search_tool per richiesta.
- Ogni chiamata web deve essere “mirata”: query breve ma specifica (società + evento + data/periodo se noto).
- Dopo 2 chiamate: NON cercare oltre. Se mancano dati, dichiaralo e prosegui con quanto disponibile.

3) POLICY KB READ (DEFAULT)
- Usa read_from_kb_tool come prima scelta quando:
  - la domanda è concettuale, procedurale, definitoria, comparativa (es. ratio, metodologia, modelli, rischio),
  - o riguarda informazioni “stabili” già salvate (note interne, sintesi, definizioni, policy).
- Se il risultato KB è vuoto o troppo generico: puoi fare 1 web_search_tool (rispettando il limite massimo).

4) POLICY KB WRITE (SOLO QUANDO SERVE DAVVERO)
- Usa write_to_kb_tool SOLO per salvare:
  - definizioni/linee guida riusabili, checklist, procedure, template,
  - sintesi stabili di fonti (non time-sensitive) oppure decisioni/assunzioni del progetto.
- NON scrivere in KB:
  - prezzi, “ultime notizie”, risultati trimestrali, contenuti che scadono rapidamente,
  - opinioni non verificabili,
  - contenuti duplicati o rumorosi.
- Prima di scrivere: verifica con read_from_kb_tool che non esista già un contenuto equivalente.
- Quando scrivi: salva testo autocontenuto e datato, con contesto minimo e tag 
(es. “FINANCE|RATIO|ROE”, “MACRO|INFLATION|EU”).

5) POLICY STOCK SCORING (QUANDO USARLO)
- Usa stock_scoring_tool quando l utente chiede:
  - “score”, “BUY/HOLD/SELL”, “valutazione rapida”, “screening”, “analisi indicatori base”.
- Non usare stock_scoring_tool per:
  - notizie, cause di movimenti di prezzo, eventi societari, o analisi qualitativa senza metriche.
- Dopo il tool:
  - riporta decisione + motivazioni sintetiche,
  - separa chiaramente: metriche osservate vs interpretazione,
  - segnala limiti: dati mancanti, settore non confrontabile, metriche distorte.


=== SICUREZZA E COMPLIANCE ===
- Non dare consulenza finanziaria personalizzata (“compra/vendi per te”): fornisci analisi informativa e rischi.
- Se l utente chiede previsioni certe: rispondi con scenari e sensitività, non certezze.

Ricorda: accuratezza > completezza. Se manca un dato, dillo.
"""

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

tool_node = ToolNode(available_tools_list)

llm = ChatOllama(
    model=settings.LLM_MODEL_NAME,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.1,
    keep_alive="4h",
    seed=42
)

llm_with_tools = llm.bind_tools(available_tools_list)

async def call_model_node(state: AgentState) -> dict:
    """Nodo 1: Il "Cervello". Chiama l'LLM (Invariato)"""
    print("--- GRAFO: Chiamo LLM ---")
    messages = state['messages']
    response_ai_message = await llm_with_tools.ainvoke(messages)
    return {"messages": [response_ai_message]}

def should_continue_edge(state: AgentState) -> str:
    """Edge Condizionale: Decide la prossima mossa (Invariato)."""
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    else:
        return "end_conversation"

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model_node)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue_edge,
    {
        "continue_to_tools": "action",
        "end_conversation": END
    }
)

workflow.add_edge("action", "agent")

app = workflow.compile()


def format_st_history_to_langchain(st_messages: list[dict]) -> list:
    """Converte la history di Streamlit (dict) nel formato LangChain (oggetti BaseMessage)."""
    history = []
    for msg in st_messages:
        role = msg["role"]
        if role == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif role == "assistant":
            history.append(AIMessage(content=msg.get("content", ""), tool_calls=msg.get("tool_calls", [])))
    return history

async def get_agent_graph_response(user_query: str, chat_history: list[dict]) -> AIMessage:
    """
    Funzione principale che invoca il grafo LangGraph (Invariata).
    """
    formatted_history = format_st_history_to_langchain(chat_history)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *formatted_history,
        HumanMessage(content=user_query),
    ]

    final_state = await app.ainvoke(
        {"messages": messages}
    )

    return final_state['messages'][-1]
