from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.orm import declarative_base

# 1. Declarative Base
#    Tutte le classi modello che creeremo erediteranno da questa classe base.
#    SQLAlchemy la userà per "scoprire" le tabelle da creare.
Base = declarative_base()


# 2. Modello della Tabella
#    Questa classe rappresenta la tabella `classified_questions` nel database.
class ClassifiedQuestion(Base):
    """
    Modello ORM per rappresentare una domanda classificata e il suo
    contenuto generato nel database.
    """

    __tablename__ = "classified_questions1"

    # --- Colonne della Tabella ---

    # ID: Chiave primaria, intero, auto-incrementante
    id = Column(Integer, primary_key=True, index=True)

    # Testo della domanda originale inserita dall'utente
    question_text = Column(Text, nullable=False)

    # Classificazione ottenuta dal modello (es. "Generale", "Tecnica", "Commerciale")
    classification = Column(Text, nullable=False, index=True)

    # Contenuto generato dalla pipeline in risposta alla domanda
    # Usiamo 'Text' invece di 'String' perché il contenuto può essere lungo.
    # 'nullable=True' significa che può essere vuoto (ad esempio, prima della generazione).
    generated_content = Column(Text, nullable=True)

    # Timestamp di creazione: si popola automaticamente con la data e ora correnti
    # quando un record viene creato per la prima volta.
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Timestamp di aggiornamento: si aggiorna automaticamente ogni volta che
    # il record viene modificato.
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """
        Rappresentazione "leggibile" dell'oggetto, utile per il debug.
        Esempio: <ClassifiedQuestion(id=1, classification='Generale')>
        """
        return f"<ClassifiedQuestion(id={self.id}, classification='{self.classification}')>"
