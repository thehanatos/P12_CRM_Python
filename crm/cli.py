import uuid
from datetime import datetime, timedelta
import click
from .database import SessionLocal, Base, engine
from .models import Client, Contract, Event, User, Role
from argon2 import PasswordHasher
from crm.auth import authenticate_user, get_current_user, require_role

ph = PasswordHasher()


# === Initialiser la base si besoin ===
Base.metadata.create_all(engine)


@click.group()
def cli():
    """CRM CLI - Gérer Clients, Contrats, Evénements"""
    pass


# === LOGIN ===
@cli.command()
@click.option('--email', prompt="Email")
@click.option('--password', prompt=True, hide_input=True)
def login(email, password):
    """Connexion pour obtenir un token JWT"""
    try:
        authenticate_user(email, password)
        click.echo("✅ Connecté ! Token sauvegardé localement.")
    except Exception as e:
        click.echo(str(e))


# === Commande : Créer un Role ===
@cli.command()
@click.option('--name', prompt="Nom du rôle (commercial/support/gestion)")
def add_role(name):
    """Créer un nouveau rôle"""
    session = SessionLocal()
    role = Role(name=name)
    session.add(role)
    session.commit()
    click.echo(f"✅ Rôle créé : {role}")
    session.close()


# === Commande : Créer un Utilisateur ===
@cli.command()
@click.option('--employee-number', prompt="Numéro d'employé")
@click.option('--name', prompt="Nom")
@click.option('--email', prompt="Email")
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--role-id', prompt="ID du rôle")
def add_user(employee_number, name, email, password, role_id):
    """Créer un nouvel utilisateur"""
    session = SessionLocal()
    role = session.get(Role, role_id)
    if not role:
        click.echo("❌ Rôle introuvable.")
        return

    user = User(
        employee_number=employee_number,
        name=name,
        email=email,
        role=role
    )
    user.set_password(password)
    session.add(user)
    session.commit()
    click.echo(f"✅ Utilisateur créé : {user}")
    session.close()


# === Commande : Créer un Client ===
@cli.command()
@require_role(["gestion"])  # vérifier qui a accès
@click.option('--name', prompt="Nom du client")
@click.option('--email', prompt="Email")
@click.option('--phone', prompt="Téléphone")
@click.option('--company', prompt="Entreprise")
@click.option('--sales-contact', prompt="Contact commercial")
def add_client(name, email, phone, company, sales_contact):
    """Ajouter un nouveau client"""
    user = get_current_user()
    session = SessionLocal()
    client = Client(
        name=name,
        email=email,
        phone=phone,
        company=company,
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        sales_contact=user['name']
    )
    session.add(client)
    session.commit()
    click.echo(f"✅ Client créé : {client}")
    session.close()


# === Commande : Créer un Contrat ===
@cli.command()
@click.option('--client-id', prompt="ID du client")
@click.option('--amount-total', prompt="Montant total", type=float)
@click.option('--amount-remaining', prompt="Montant restant", type=float)
@click.option('--status', prompt="Statut (ex: signed, pending)")
def add_contract(client_id, amount_total, amount_remaining, status):
    """Ajouter un contrat pour un client existant"""
    session = SessionLocal()
    client = session.get(Client, client_id)
    if not client:
        click.echo("❌ Client non trouvé.")
        return

    contract = Contract(
        unique_id=str(uuid.uuid4()),
        client_id=client.id,
        sales_contact=client.sales_contact,
        amount_total=amount_total,
        amount_remaining=amount_remaining,
        created_at=datetime.utcnow(),
        status=status
    )
    session.add(contract)
    session.commit()
    click.echo(f"✅ Contrat créé : {contract}")
    session.close()


# === Commande : Créer un Événement ===
@cli.command()
@click.option('--contract-id', prompt="ID du contrat")
@click.option('--start-days', prompt="Jours à partir d'aujourd'hui pour START", type=int)
@click.option('--end-days', prompt="Jours à partir d'aujourd'hui pour END", type=int)
@click.option('--support-contact', prompt="Contact support")
@click.option('--location', prompt="Lieu")
@click.option('--attendees', prompt="Nombre de participants", type=int)
@click.option('--notes', prompt="Notes")
def add_event(contract_id, start_days, end_days, support_contact, location, attendees, notes):
    """Ajouter un événement pour un contrat existant"""
    session = SessionLocal()
    contract = session.get(Contract, contract_id)
    if not contract:
        click.echo("❌ Contrat non trouvé.")
        return

    client = contract.client

    event = Event(
        contract_id=contract.id,
        client_name=client.name,
        client_contact=f"{client.phone} | {client.email}",
        event_date_start=datetime.utcnow() + timedelta(days=start_days),
        event_date_end=datetime.utcnow() + timedelta(days=end_days),
        support_contact=support_contact,
        location=location,
        attendees=attendees,
        notes=notes
    )
    session.add(event)
    session.commit()
    click.echo(f"✅ Événement créé : {event}")
    session.close()


@cli.command()
@require_role(["gestion"])  # Seuls les rôles "gestion" peuvent exécuter
def list_users():
    """Lister les utilisateurs (seulement pour 'gestion')"""
    session = SessionLocal()
    users = session.query(User).all()
    for u in users:
        click.echo(f"{u.id}: {u.name} ({u.email}) - {u.role.name if u.role else 'Aucun rôle'}")
    session.close()


@cli.command()
def whoami():
    """Affiche l'utilisateur connecté"""
    try:
        user = get_current_user()
        click.echo(f"👤 Connecté en tant que : {user['name']} | rôle : {user['role']}")
    except Exception as e:
        click.echo(str(e))


# === Commande : Lister Clients, Contrats, Événements ===
@cli.command()
def list_all():
    """Lister tous les clients, contrats et événements"""
    session = SessionLocal()
    clients = session.query(Client).all()
    contracts = session.query(Contract).all()
    events = session.query(Event).all()

    click.echo("\n=== Clients ===")
    for c in clients:
        click.echo(f"- {c.id}: {c.name} ({c.email})")

    click.echo("\n=== Contrats ===")
    for c in contracts:
        click.echo(f"- {c.id}: {c.unique_id} (Client ID: {c.client_id}, Montant: {c.amount_total})")

    click.echo("\n=== Événements ===")
    for e in events:
        click.echo(f"- {e.id}: {e.client_name} (Début: {e.event_date_start}, Lieu: {e.location})")

    session.close()


@cli.command()
def logout():
    """Déconnexion : supprime le token local"""
    import os
    try:
        os.remove(".token")
        click.echo("✅ Déconnecté(e).")
    except FileNotFoundError:
        click.echo("ℹ️  Aucun token trouvé : vous êtes déjà déconnecté(e).")


if __name__ == '__main__':
    cli()
