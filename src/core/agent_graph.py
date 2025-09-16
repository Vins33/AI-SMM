# Percorso file: src/core/agent_graph.py
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

# Importiamo il ToolNode pre-costruito
from langgraph.prebuilt import ToolNode

# Importiamo i nostri tool personalizzati e le settings del progetto
from src.core.agent_tools import available_tools_list  # Questa è già la tua "lista di BaseTools"
from src.core.config import settings


# --- 1. Definizione dello Stato dell'Agente (Invariato) ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# --- 2. Inizializzazione Componenti ---

# Non usiamo più ToolExecutor.
# Creiamo direttamente il NODO dei tool.
# available_tools_list (che viene da agent_tools.py) è già una lista
# di BaseTools (perché il decoratore @tool li converte automaticamente).
tool_node = ToolNode(available_tools_list)

# LLM: (Invariato)
llm = ChatOllama(
    model=settings.LLM_MODEL_NAME,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.1,
    keep_alive="4h",
    seed=42
)

# Associazione Tool: (Invariato)
llm_with_tools = llm.bind_tools(available_tools_list)

# --- 3. Definizione dei Nodi del Grafo ---

async def call_model_node(state: AgentState) -> dict:
    """Nodo 1: Il "Cervello". Chiama l'LLM (Invariato)"""
    print("--- GRAFO: Chiamo LLM ---")
    messages = state['messages']
    response_ai_message = await llm_with_tools.ainvoke(messages)
    return {"messages": [response_ai_message]}

# *** NON ABBIAMO PIÙ BISOGNO DI 'call_tools_node' ***
# Il 'tool_node' che abbiamo importato è già una funzione nodo valida.

# --- 4. Definizione della Logica Condizionale (Invariato) ---

def should_continue_edge(state: AgentState) -> str:
    """Edge Condizionale: Decide la prossima mossa (Invariato)."""
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    else:
        return "end_conversation"

# --- 5. Costruzione e Compilazione del Grafo ---

workflow = StateGraph(AgentState)

# Aggiungiamo i nodi
workflow.add_node("agent", call_model_node)
# Usiamo direttamente il tool_node come nodo "action"
workflow.add_node("action", tool_node)

# Definiamo il punto di ingresso
workflow.set_entry_point("agent")

# Aggiungiamo l'edge condizionale (Invariato)
workflow.add_conditional_edges(
    "agent",
    should_continue_edge,
    {
        "continue_to_tools": "action",
        "end_conversation": END
    }
)

# Aggiungiamo il loop (Invariato)
workflow.add_edge("action", "agent")

# Compiliamo il grafo (Invariato)
app = workflow.compile()


# --- 6. Funzione Wrapper e Helper per la UI (Invariato) ---

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
    current_messages = formatted_history + [HumanMessage(content=user_query)]

    final_state = await app.ainvoke(
        {"messages": current_messages}
    )

    return final_state['messages'][-1]
