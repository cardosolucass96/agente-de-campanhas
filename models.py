from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Message(Base):
    """
    Modelo para armazenar mensagens recebidas e enviadas
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    instance = Column(String(100))
    remote_jid = Column(String(100), index=True)
    message_id = Column(String(255), index=True)
    direction = Column(String(20), index=True)  # 'incoming' ou 'outgoing'
    from_me = Column(Boolean, default=False)
    text = Column(Text)
    status = Column(String(50), default="pending")  # pending, sent, delivered, read, failed
    raw_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relacionamento com contato
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    contact = relationship("Contact", back_populates="messages")
    
    # Relacionamento com conversação
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True)
    conversation = relationship("Conversation", back_populates="messages")

class Conversation(Base):
    """
    Modelo para agrupar mensagens em conversações
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    contact = relationship("Contact", back_populates="conversations")
    
    status = Column(String(50), default="active")  # active, closed, archived
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadados da conversa
    context = Column(JSON)  # Para armazenar contexto da conversa para o LangGraph
    summary = Column(Text, nullable=True)  # Resumo da conversa
    
    # Relacionamento com mensagens
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

class Campaign(Base):
    """
    Modelo para campanhas de mensagens
    """
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="draft")  # draft, active, paused, completed
    target_audience = Column(JSON)
    message_template = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class Contact(Base):
    """
    Modelo para contatos
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200))
    contact_metadata = Column(JSON)  # Renomeado de 'metadata' para 'contact_metadata'
    tags = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    messages = relationship("Message", back_populates="contact")
    conversations = relationship("Conversation", back_populates="contact")

class AgentLog(Base):
    """
    Modelo para logs de ações do agente
    """
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True)
    action = Column(String(100))  # process_message, send_message, error, etc
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(50))  # success, error, pending
    error_message = Column(Text, nullable=True)
    execution_time = Column(Integer, nullable=True)  # em milissegundos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
