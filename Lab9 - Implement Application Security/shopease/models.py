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
    customerID = Column("customerid", Integer, primary_key=True)
    firstName = Column("firstname", String(255), nullable=False)
    lastName = Column("lastname", String(255), nullable=False)
    email = Column("email", String(255), nullable=False, unique=True)
    phone = Column("phone", String(20))
    address = Column("address", String(255))
    # store hashed password
    password = Column("password", String(255))
    # role: either 'customer', 'agent', or 'manager'
    role = Column("role", String(50), default="customer")

    tickets = relationship("SupportTicket", back_populates="customer")
    notifications = relationship("Notification", back_populates="customer")


class SupportAgent(Base):
    __tablename__ = "supportagents"
    agentID = Column("agentid", Integer, primary_key=True)
    firstName = Column("firstname", String(255))
    lastName = Column("lastname", String(255))
    email = Column("email", String(255))

    tickets = relationship("SupportTicket", back_populates="supportAgent")


class Manager(Base):
    __tablename__ = "managers"
    managerID = Column("managerid", Integer, primary_key=True)
    firstName = Column("firstname", String(255))
    lastName = Column("lastname", String(255))
    email = Column("email", String(255))
    permissions = Column("permissions", String(255))


class SupportTicket(Base):
    __tablename__ = "supporttickets"
    ticketID = Column("ticketid", Integer, primary_key=True)
    customerID = Column("customerid", Integer, ForeignKey("customers.customerid"), nullable=False)
    supportAgentID = Column("supportagentid", Integer, ForeignKey("supportagents.agentid"), nullable=True)
    issueDescription = Column("issuedescription", Text)
    createdAt = Column("createdat", DateTime, default=datetime.datetime.utcnow)
    status = Column("status", Enum(TicketStatus), default=TicketStatus.open)

    customer = relationship("Customer", back_populates="tickets")
    supportAgent = relationship("SupportAgent", back_populates="tickets")
    attachments = relationship("Attachment", back_populates="ticket")
    responses = relationship("AIResponse", back_populates="ticket")


class Attachment(Base):
    __tablename__ = "attachments"
    attachmentID = Column("attachmentid", Integer, primary_key=True)
    ticketID = Column("ticketid", Integer, ForeignKey("supporttickets.ticketid"), nullable=False)
    type = Column("type", Enum(AttachmentType))
    filePath = Column("filepath", String(255))
    transcription = Column("transcription", Text)

    ticket = relationship("SupportTicket", back_populates="attachments")


class AIResponse(Base):
    __tablename__ = "airesponses"
    responseID = Column("responseid", Integer, primary_key=True)
    ticketID = Column("ticketid", Integer, ForeignKey("supporttickets.ticketid"), nullable=False)
    generatedText = Column("generatedtext", Text)
    confidenceScore = Column("confidencescore", Float)
    timestamp = Column("timestamp", DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="responses")


class Notification(Base):
    __tablename__ = "notifications"
    notificationID = Column("notificationid", Integer, primary_key=True)
    customerID = Column("customerid", Integer, ForeignKey("customers.customerid"), nullable=False)
    type = Column("type", Enum(NotificationType))
    message = Column("message", String(255))
    sentAt = Column("sentat", DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="notifications")
