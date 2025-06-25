import uuid
from datetime import datetime, timedelta
import click
from .database import SessionLocal, Base, engine
from .models import Client, Contract, Event, User, Role
from argon2 import PasswordHasher
from crm.auth import authenticate_user, get_current_user, require_role, require_auth

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
@require_auth
@require_role(["gestion"])
def add_role(name):
    """Créer un nouveau rôle"""
    session = SessionLocal()
    name = click.prompt("Nom du rôle (commercial/support/gestion)")
    role = Role(name=name)
    session.add(role)
    session.commit()
    click.echo(f"✅ Rôle créé : {role}")
    session.close()


# === Commande : Créer un Utilisateur ===
@cli.command()
@require_auth
@require_role(["gestion"])
def add_user(user):
    """Créer un nouvel utilisateur"""
    employee_number = click.prompt("Numéro d'employé")
    name = click.prompt("Nom")
    email = click.prompt("Email")
    password = click.prompt("Mot de passe", hide_input=True, confirmation_prompt=True)
    role_name = click.prompt("Rôle (commercial / support / gestion)")
    session = SessionLocal()
    role = session.query(Role).filter_by(name=role_name).first()
    if not role:
        click.echo(f"❌ Rôle '{role_name}' introuvable.")
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
@require_auth
@require_role(["commercial"])
def add_client(user):
    """Ajouter un nouveau client (auth requis)."""

    name = click.prompt("Nom du client")
    email = click.prompt("Email")
    phone = click.prompt("Téléphone")
    company = click.prompt("Entreprise")
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
@require_auth
@require_role(["gestion"])
def add_contract(user):
    """Ajouter un contrat pour un client existant"""
    client_id = click.prompt("ID du client")
    amount_total = click.prompt("Montant total")
    amount_remaining = click.prompt("Montant restant")
    status = click.prompt("Statut (ex: signed, pending)")
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


# === Commande : Modifier un de ses Contrats (commercial) ou Tous (gestion)===
@cli.command()
@require_auth
@require_role(["gestion", "commercial"])
def update_contract(user):
    """Modifier un contrat existant (gestion = tous, commercial = uniquement les siens)"""
    session = SessionLocal()
    # Récupérer le nom du rôle
    user_role = user.get('role')

    if user_role == "gestion":
        contracts = session.query(Contract).all()
    elif user_role == "commercial":
        contracts = session.query(Contract).filter_by(sales_contact=user.get('name')).all()
    else:
        click.echo("❌ Vous n'avez pas les droits pour modifier les contrats.")
        return

    if not contracts:
        click.echo("❌ Aucun contrat trouvé.")
        return

    click.echo("\n📄 Liste des contrats :")
    for c in contracts:
        click.echo(f"  ID: {c.id} | Client ID: {c.client_id} | Montant: {c.amount_total} | Statut: {c.status}")

    contract_id = click.prompt("ID du contrat à modifier")

    contract = session.get(Contract, contract_id)
    if not contract:
        click.echo("❌ Contrat non trouvé")
        return

    # Pour les commerciaux, vérifier qu'ils ne modifient que leurs contrats
    if user_role == "commercial" and contract.sales_contact != user.get('name'):
        click.echo("❌ Vous ne pouvez modifier que vos propres contrats.")
        return

    # Afficher les statuts disponibles (exemple)
    VALID_STATUSES = ["new", "pending", "signed", "cancelled"]
    click.echo(f"📌 Statuts disponibles : {', '.join(VALID_STATUSES)}")
    click.echo(f"🔎 Contrat actuel : {contract}")
    # Prompts facultatifs — laisser vide pour ne pas modifier
    new_amount_total = click.prompt("Nouveau montant total", default=contract.amount_total, show_default=True)
    new_amount_remaining = click.prompt("Nouveau montant restant",
                                        default=contract.amount_remaining, show_default=True)

    while True:
        new_status = click.prompt("Nouveau statut", default=contract.status, show_default=True)
        if new_status in VALID_STATUSES:
            break
        click.echo("❌ Statut invalide. Choisissez parmi : " + ", ".join(VALID_STATUSES))

    contract.amount_total = float(new_amount_total)
    contract.amount_remaining = float(new_amount_remaining)
    contract.status = new_status
    contract.last_updated = datetime.utcnow()

    session.commit()
    click.echo(f"✅ Contrat mis à jour : {contract}")
    session.close()


# === Commande : Créer un Événement ===
@cli.command()
@require_auth
@require_role(["commercial"])
def add_event(user):
    """Ajouter un événement pour un contrat existant"""
    contract_id = click.prompt("ID du contrat")
    start_days = click.prompt("Jours à partir d'aujourd'hui pour START")
    end_days = click.prompt("Jours à partir d'aujourd'hui pour END")
    support_contact = click.prompt("Contact support")
    location = click.prompt("Lieu")
    attendees = click.prompt("Nombre de participants")
    notes = click.prompt("Notes")
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
@require_role(["gestion"])
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
