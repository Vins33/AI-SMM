from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, relationship

# 1. Declarative Base
#    Tutte le classi modello che creeremo erediteranno da questa classe base.
#    SQLAlchemy la userà per "scoprire" le tabelle da creare.
Base = declarative_base()


# Modello per le conversazioni dell'agente finanziario
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, default="Nuova conversazione")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # "user" o "agent"
    content = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
