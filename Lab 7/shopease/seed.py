from .db import init_engine, get_session, create_schema
from .models import (
    Customer,
    SupportAgent,
    Manager,
    SupportTicket,
    Attachment,
    AIResponse,
    Notification,
    TicketStatus,
    AttachmentType,
    NotificationType,
)
import os


def seed_all(database_url: str | None = None):
    init_engine(database_url)
    # ensure tables exist
    create_schema()
    session = get_session()


    # customers
    c1 = Customer(firstName="Alice", lastName="Smith", email="alice@example.com", phone="1234567890", address="1 Main St", password="pass")
    c2 = Customer(firstName="Bob", lastName="Jones", email="bob@example.com", phone="0987654321", address="2 High St", password="pass")
    session.add_all([c1, c2])
    session.commit()

    # agents and managers
    a1 = SupportAgent(firstName="Tom", lastName="Agent", email="tom.agent@example.com")
    a2 = SupportAgent(firstName="Sara", lastName="Agent", email="sara.agent@example.com")
    m1 = Manager(firstName="Manny", lastName="Manager", email="manny.manager@example.com", permissions="all")
    session.add_all([a1, a2, m1])
    session.commit()

    # tickets
    t1 = SupportTicket(customerID=c1.customerID, supportAgentID=a1.agentID, issueDescription="Cannot checkout", status=TicketStatus.open)
    t2 = SupportTicket(customerID=c2.customerID, supportAgentID=a2.agentID, issueDescription="Payment failed", status=TicketStatus.pending)
    session.add_all([t1, t2])
    session.commit()

    # attachments
    at1 = Attachment(ticketID=t1.ticketID, type=AttachmentType.log, filePath="/tmp/log1.txt", transcription=None)
    at2 = Attachment(ticketID=t2.ticketID, type=AttachmentType.image, filePath="/tmp/screenshot.png", transcription=None)
    session.add_all([at1, at2])
    session.commit()

    # ai responses
    r1 = AIResponse(ticketID=t1.ticketID, generatedText="Try clearing cache", confidenceScore=0.85)
    session.add(r1)
    session.commit()

    # notifications
    n1 = Notification(customerID=c1.customerID, type=NotificationType.email, message="Your ticket was created")
    session.add(n1)
    session.commit()

    session.close()
    print("Seeded sample data")


if __name__ == "__main__":
    seed_all()
