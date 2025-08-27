from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(32), nullable=False, unique=True, index=True)
    name = Column(String(120))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    tickets = relationship("Ticket", back_populates="customer")
    session = relationship("SessionState", uselist=False, back_populates="customer")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=False)
    category = Column(String(100), nullable=False)
    initial_message = Column(Text)
    media_url = Column(String(1024), nullable=True)
    chatwoot_conversation_id = Column(BigInteger, unique=True, index=True)
    status = Column(String(50), default="open")
    satisfaction_rating = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    customer = relationship("Customer", back_populates="tickets")

class SessionState(Base):
    __tablename__ = "session_states"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id"), nullable=False, unique=True)
    state = Column(String(64), default="start")
    data_json = Column(Text, default="{}")
    customer = relationship("Customer", back_populates="session")