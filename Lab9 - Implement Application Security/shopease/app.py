from fastapi import FastAPI
import os
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Support running this file either as part of the package (recommended)
# or directly as a script (so relative imports would fail). Try package
# (relative) imports first and fall back to direct module imports.
try:
    from .db import init_engine, get_session
    from .models import SupportTicket, TicketStatus, Customer, SupportAgent
except Exception:
    # fallback when running the file directly (python shopease/app.py)
    from db import init_engine, get_session
    from models import SupportTicket, TicketStatus, Customer, SupportAgent

# Initialize engine (use DATABASE_URL env or fallback to local sqlite file)
DATABASE_URL = os.environ.get("DATABASE_URL")
init_engine(DATABASE_URL)

app = FastAPI()
# Enable CORS for development/testing. In production, restrict origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from pydantic import BaseModel
from fastapi import HTTPException, status as http_status
from . import auth
from fastapi import Depends
from .auth import Token


def ticket_to_dict(ticket: SupportTicket) -> dict:
    cust = None
    agent = None
    if ticket.customer:
        cust = {
            "customerID": ticket.customer.customerID,
            "firstName": ticket.customer.firstName,
            "lastName": ticket.customer.lastName,
            "email": ticket.customer.email,
        }
    if ticket.supportAgent:
        agent = {
            "agentID": ticket.supportAgent.agentID,
            "firstName": ticket.supportAgent.firstName,
            "lastName": ticket.supportAgent.lastName,
            "email": ticket.supportAgent.email,
        }
    return {
        "ticketID": ticket.ticketID,
        "issueDescription": ticket.issueDescription,
        "createdAt": ticket.createdAt,
        "status": ticket.status.name if ticket.status is not None else None,
        "customer": cust,
        "supportAgent": agent,
    }


def get_all_tickets():
    session = get_session()
    try:
        tickets = (
            session.query(SupportTicket)
            .order_by(SupportTicket.createdAt.desc())
            .all()
        )
        return [ticket_to_dict(t) for t in tickets]
    finally:
        session.close()


def customer_to_dict(cust: Customer) -> dict:
    if cust is None:
        return None
    return {
        "customerID": cust.customerID,
        "firstName": cust.firstName,
        "lastName": cust.lastName,
        "email": cust.email,
        "phone": cust.phone,
        "address": cust.address,
    }


def _extract_city_from_address(address: str) -> str:
    """Try to extract a city substring from a freeform address.

    Strategy (best-effort):
    - If address contains commas, take the second segment (after first comma) and strip it.
    - Otherwise return empty string.

    This is a heuristic because the data model stores address as a single string.
    """
    if not address:
        return ""
    # split on comma and return second piece if available
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[1]
    return ""


@app.get("/adsweb/api/v1/tickets")
def read_tickets():
    return get_all_tickets()


@app.get("/adsweb/api/v1/tickets/{ticket_id}")
def read_ticket(ticket_id: int):
    # Validate ticket_id
    if ticket_id is None or ticket_id <= 0:
        raise HTTPException(status_code=400, detail="ticket_id must be a positive integer")

    session = get_session()
    try:
        ticket = session.query(SupportTicket).filter(SupportTicket.ticketID == ticket_id).first()
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket with id {ticket_id} not found")
        return ticket_to_dict(ticket)
    finally:
        session.close()


@app.get("/adsweb/api/v1/customer/search/{searchString}")
def search_customers(searchString: str):
    """Search customers by firstName, lastName, email, phone or address.

    Performs case-insensitive partial match across multiple fields and
    returns a list of customer dicts.
    """
    if searchString is None or searchString.strip() == "":
        raise HTTPException(status_code=400, detail="searchString must be a non-empty string")

    session = get_session()
    try:
        # Use ilike for case-insensitive partial matching (works for sqlite/postgres)
        pattern = f"%{searchString}%"
        results = (
            session.query(Customer)
            .filter(
                (Customer.firstName.ilike(pattern))
                | (Customer.lastName.ilike(pattern))
                | (Customer.email.ilike(pattern))
                | (Customer.phone.ilike(pattern))
                | (Customer.address.ilike(pattern))
            )
            .all()
        )

        return [customer_to_dict(c) for c in results]
    finally:
        session.close()


@app.get("/adsweb/api/v1/customer/addresses")
def list_addresses():
    """Return a list of addresses with customer data, sorted ascending by city.

    Because `Customer.address` is a freeform string, we heuristically extract
    the city by taking the second comma-separated segment (if present). The
    response is a list of objects with keys: address, city, customer.
    """
    session = get_session()
    try:
        customers = session.query(Customer).all()

        results = []
        for c in customers:
            city = _extract_city_from_address(c.address)
            results.append({
                "address": c.address,
                "city": city,
                "customer": customer_to_dict(c),
            })

        # sort by city (case-insensitive); empty cities sort first
        results.sort(key=lambda r: (r["city"].lower() if r["city"] else ""))
        return results
    finally:
        session.close()


class TicketCreate(BaseModel):
    customerID: int
    issueDescription: str
    supportAgentID: int | None = None
    status: str | None = None


class TicketUpdate(BaseModel):
    customerID: int | None = None
    issueDescription: str | None = None
    supportAgentID: int | None = None
    status: str | None = None


@app.post("/adsweb/api/v1/ticket", status_code=http_status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user=Depends(auth.get_current_user)):
    # Validate payload.customerID exists
    session = get_session()
    try:
        customer = session.query(Customer).filter(Customer.customerID == payload.customerID).first()
        if customer is None:
            raise HTTPException(status_code=400, detail=f"Customer with id {payload.customerID} does not exist")

        # Validate support agent if provided
        if payload.supportAgentID is not None:
            agent = session.query(SupportAgent).filter(SupportAgent.agentID == payload.supportAgentID).first()
            if agent is None:
                raise HTTPException(status_code=400, detail=f"SupportAgent with id {payload.supportAgentID} does not exist")

        # Parse status if provided, otherwise default is TicketStatus.open
        status_enum = None
        if payload.status:
            try:
                status_enum = TicketStatus(payload.status)
            except Exception:
                valid = ", ".join([e.value for e in TicketStatus])
                raise HTTPException(status_code=400, detail=f"Invalid status. Valid values: {valid}")

        new_ticket = SupportTicket(
            customerID=payload.customerID,
            supportAgentID=payload.supportAgentID,
            issueDescription=payload.issueDescription,
            status=(status_enum or TicketStatus.open),
        )
        session.add(new_ticket)
        session.commit()
        session.refresh(new_ticket)

        return ticket_to_dict(new_ticket)
    finally:
        session.close()



class SignupPayload(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str
    role: str | None = "customer"


@app.post("/adsweb/api/v1/signup", status_code=http_status.HTTP_201_CREATED)
def signup(payload: SignupPayload):
    session = get_session()
    try:
        existing = session.query(Customer).filter(Customer.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = auth.get_password_hash(payload.password)
        user = Customer(firstName=payload.firstName, lastName=payload.lastName, email=payload.email, password=hashed, role=payload.role or "customer")
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"email": user.email, "role": user.role}
    finally:
        session.close()


from fastapi.security import OAuth2PasswordRequestForm


@app.post("/adsweb/api/v1/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow compatible token endpoint.

    Accepts form fields: username, password, scope, grant_type, client_id.
    Returns: { access_token, token_type }
    """
    session = get_session()
    try:
        user = auth.authenticate_user(session, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = auth.create_access_token({"sub": user.email, "role": user.role})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        session.close()


@app.post("/adsweb/api/v1/login")
def login(payload: dict):
    # simple JSON login: {"username": "...", "password": "..."}
    username = payload.get("username") or payload.get("email")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username/email and password required")
    session = get_session()
    try:
        user = session.query(Customer).filter(Customer.email == username).first()
        if not user or not auth.verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = auth.create_access_token({"sub": user.email, "role": user.role})
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        session.close()


@app.put("/adsweb/api/v1/ticket/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdate):
    # Validate ticket_id
    if ticket_id is None or ticket_id <= 0:
        raise HTTPException(status_code=400, detail="ticket_id must be a positive integer")

    session = get_session()
    try:
        ticket = session.query(SupportTicket).filter(SupportTicket.ticketID == ticket_id).first()
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket with id {ticket_id} not found")

        # Apply updates if provided
        if payload.customerID is not None:
            cust = session.query(Customer).filter(Customer.customerID == payload.customerID).first()
            if cust is None:
                raise HTTPException(status_code=400, detail=f"Customer with id {payload.customerID} does not exist")
            ticket.customerID = payload.customerID

        if payload.supportAgentID is not None:
            if payload.supportAgentID:
                agent = session.query(SupportAgent).filter(SupportAgent.agentID == payload.supportAgentID).first()
                if agent is None:
                    raise HTTPException(status_code=400, detail=f"SupportAgent with id {payload.supportAgentID} does not exist")
            ticket.supportAgentID = payload.supportAgentID

        if payload.issueDescription is not None:
            ticket.issueDescription = payload.issueDescription

        if payload.status is not None:
            try:
                ticket.status = TicketStatus(payload.status)
            except Exception:
                valid = ", ".join([e.value for e in TicketStatus])
                raise HTTPException(status_code=400, detail=f"Invalid status. Valid values: {valid}")

        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket_to_dict(ticket)
    finally:
        session.close()


@app.delete("/adsweb/api/v1/ticket/{ticket_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int):
    # Validate ticket_id
    if ticket_id is None or ticket_id <= 0:
        raise HTTPException(status_code=400, detail="ticket_id must be a positive integer")

    session = get_session()
    try:
        ticket = session.query(SupportTicket).filter(SupportTicket.ticketID == ticket_id).first()
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket with id {ticket_id} not found")

        session.delete(ticket)
        session.commit()
        # 204 No Content
        return None
    finally:
        session.close()


if __name__ == "__main__":
    # simple manual run for development: run the app object directly so
    # uvicorn doesn't need to import the package by name.
    import uvicorn

    # Do not set reload=True when running the app object directly; reload
    # requires uvicorn to import the app by string and will error.
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
