from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

Base = declarative_base()


class TicketStatus(enum.Enum):
    open = "open"
    closed = "closed"
    pending = "pending"


class NotificationType(enum.Enum):
    email = "email"
    sms = "sms"


class AttachmentType(enum.Enum):
    image = "image"
    log = "log"
    other = "other"


class Customer(Base):
    __tablename__ = "customers"
    customerID = Column(Integer, primary_key=True)
    firstName = Column(String(255), nullable=False)
    lastName = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    address = Column(String(255))
    password = Column(String(255))

    tickets = relationship("SupportTicket", back_populates="customer")
    notifications = relationship("Notification", back_populates="customer")


class SupportAgent(Base):
    __tablename__ = "supportagents"
    agentID = Column(Integer, primary_key=True)
    firstName = Column(String(255))
    lastName = Column(String(255))
    email = Column(String(255))

    tickets = relationship("SupportTicket", back_populates="supportAgent")


class Manager(Base):
    __tablename__ = "managers"
    managerID = Column(Integer, primary_key=True)
    firstName = Column(String(255))
    lastName = Column(String(255))
    email = Column(String(255))
    permissions = Column(String(255))


class SupportTicket(Base):
    __tablename__ = "supporttickets"
    ticketID = Column(Integer, primary_key=True)
    customerID = Column(Integer, ForeignKey("customers.customerID"), nullable=False)
    supportAgentID = Column(Integer, ForeignKey("supportagents.agentID"), nullable=True)
    issueDescription = Column(Text)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)

    customer = relationship("Customer", back_populates="tickets")
    supportAgent = relationship("SupportAgent", back_populates="tickets")
    attachments = relationship("Attachment", back_populates="ticket")
    responses = relationship("AIResponse", back_populates="ticket")


class Attachment(Base):
    __tablename__ = "attachments"
    attachmentID = Column(Integer, primary_key=True)
    ticketID = Column(Integer, ForeignKey("supporttickets.ticketID"), nullable=False)
    type = Column(Enum(AttachmentType))
    filePath = Column(String(255))
    transcription = Column(Text)

    ticket = relationship("SupportTicket", back_populates="attachments")


class AIResponse(Base):
    __tablename__ = "airesponses"
    responseID = Column(Integer, primary_key=True)
    ticketID = Column(Integer, ForeignKey("supporttickets.ticketID"), nullable=False)
    generatedText = Column(Text)
    confidenceScore = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="responses")


class Notification(Base):
    __tablename__ = "notifications"
    notificationID = Column(Integer, primary_key=True)
    customerID = Column(Integer, ForeignKey("customers.customerID"), nullable=False)
    type = Column(Enum(NotificationType))
    message = Column(String(255))
    sentAt = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="notifications")
