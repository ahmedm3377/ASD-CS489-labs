import click
import os
from .db import init_engine, create_schema, get_session
from . import seed as seed_module
from .models import Customer, SupportTicket


def ensure_engine():
    try:
        init_engine()
    except RuntimeError as e:
        raise click.ClickException(str(e))


@click.group()
def cli():
    """Shopease CLI"""


@cli.command()
@click.option("--database-url", default=None, help="Database URL to use")
def init_db(database_url):
    """Initialize the database schema"""
    init_engine(database_url)
    create_schema()
    click.echo("Database schema created")


@cli.command()
@click.option("--database-url", default=None, help="Database URL to use")
def seed(database_url):
    """Seed sample data"""
    seed_module.seed_all(database_url)


@cli.group()
def customers():
    """Manage customers"""


@customers.command("list")
def list_customers():
    ensure_engine()
    s = get_session()
    rows = s.query(Customer).all()
    for r in rows:
        click.echo(f"{r.customerID}: {r.firstName} {r.lastName} <{r.email}>")
    s.close()


@customers.command("create")
@click.option("--first-name", "first_name", required=True)
@click.option("--last-name", "last_name", required=True)
@click.option("--email", "email", required=True)
def create_customer(first_name, last_name, email):
    """Create a new customer"""
    ensure_engine()
    s = get_session()
    c = Customer(firstName=first_name, lastName=last_name, email=email)
    s.add(c)
    s.commit()
    click.echo(f"Created customer {c.customerID}")
    s.close()


@cli.group()
def tickets():
    """Manage tickets"""


@tickets.command("list")
def list_tickets():
    ensure_engine()
    s = get_session()
    rows = s.query(SupportTicket).all()
    for r in rows:
        click.echo(f"{r.ticketID}: customer={r.customerID} agent={r.supportAgentID} status={r.status}")
    s.close()


if __name__ == "__main__":
    cli()
