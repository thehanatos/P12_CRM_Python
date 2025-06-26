import uuid
from datetime import datetime, timedelta
import click
from .database import SessionLocal, Base, engine
from .models import Client, Contract, Event, User, Role
from argon2 import PasswordHasher
from crm.auth import authenticate_user, get_current_user, require_role, require_auth
from sqlalchemy import or_
from tests.validators import check_email, check_phone, check_role, check_company
from tests.validators import check_number, check_status, check_amount

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


# Générer le numero employé
def generate_next_employee_number(session):
    existing_numbers = session.query(User.employee_number).all()
    prefix = "EMP"
    max_num = 0

    for (emp_num,) in existing_numbers:
        if emp_num and emp_num.startswith(prefix):
            try:
                num_part = int(emp_num.replace(prefix, ""))
                if num_part > max_num:
                    max_num = num_part
            except ValueError:
                continue

    next_number = f"{prefix}{str(max_num + 1).zfill(3)}"
    return next_number


def prompt_until_valid(prompt_text, validator_func, error_msg="Entrée invalide."):
    while True:
        value = click.prompt(prompt_text, default="", show_default=False)
        if validator_func(value):
            return value
        click.echo(f"❌ {error_msg}")


# === Commande : Créer un Role ===
@cli.command()
@require_auth
@require_role(["gestion"])
def add_role(name):
    """Créer un nouveau rôle"""
    session = SessionLocal()
    role_name = prompt_until_valid("Role", check_role, "Role invalide")
    role = Role(name=role_name)
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
    session = SessionLocal()

    users = session.query(User).all()
    click.echo("\n📄 Liste des utilisateurs :")
    for u in users:
        click.echo(f"  ID: {u.id} | N°: {u.employee_number} | Nom: {u.name} | Rôle: {u.role.name} | Email: {u.email}")

    employee_number = generate_next_employee_number(session)
    name = click.prompt("Nom")
    email = prompt_until_valid("Email", check_email, "Email invalide")
    password = click.prompt("Mot de passe", hide_input=True, confirmation_prompt=True)
    role_name = prompt_until_valid("Role commercial/gestion/support", check_role, "Role invalide")
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


# === Commande : Modifier un Utilisateur ===
@cli.command()
@require_auth
@require_role(["gestion"])
def update_user(user):
    """Modifier un utilisateur"""
    session = SessionLocal()

    users = session.query(User).all()
    click.echo("\n📄 Liste des utilisateurs :")
    for u in users:
        click.echo(f"  ID: {u.id} | Numéro: {u.employee_number} | Nom: {u.name} | Rôle: {u.role.name}")

    user_id = prompt_until_valid("ID de l'utilisateur à modifier", check_number, "ID invalide")
    target_user = session.get(User, user_id)
    if not target_user:
        click.echo("❌ Utilisateur non trouvé")
        return

    # Prompts optionnels : laisser vide pour ne pas modifier
    # new_email = click.prompt("Nouveau email ", default="", show_default=False)
    new_email = prompt_until_valid("Email", check_email, "Email invalide")
    new_name = click.prompt("Nouveau nom ", default="", show_default=False)
    role_name = prompt_until_valid("Role", check_role, "Role invalide")
    new_password = click.prompt("Nouveau mot de passe ",
                                hide_input=True, confirmation_prompt=True, default="", show_default=False)

    if new_email:
        target_user.email = new_email
    if new_name:
        target_user.name = new_name
    if role_name:
        role = session.query(Role).filter_by(name=role_name).first()
        if not role:
            click.echo("❌ Rôle introuvable.")
            return
        target_user.role = role
    if new_password:
        target_user.set_password(new_password)

    session.commit()
    click.echo(f"✅ Utilisateur modifié : {target_user}")
    session.close()


# === Commande : Supprimer un Utilisateur ===
@cli.command()
@require_auth
@require_role(["gestion"])
def delete_user(user):
    """Supprimer un user """
    session = SessionLocal()
    users = session.query(User).all()
    click.echo("\n📄 Liste des utilisateurs :")
    for u in users:
        click.echo(f"  ID: {u.id} | Numéro: {u.employee_number} | Nom: {u.name} | Rôle: {u.role.name}")

    user_id = prompt_until_valid("ID de l'utilisateur à supprimer", check_number, "ID invalide")
    target_user = session.get(User, user_id)
    if not target_user:
        click.echo("❌ Utilisateur non trouvé")
        return

    if not click.confirm(f"⚠️ Êtes-vous sûr de vouloir supprimer l'utilisateur '{target_user.name}' ?", default=False):
        click.echo("❌ Suppression annulée.")
        return

    session.delete(target_user)
    session.commit()
    click.echo(f"✅ Utilisateur supprimé : {target_user}")
    session.close()


# === Commande : Créer un Client ===
@cli.command()
@require_auth
@require_role(["commercial"])
def add_client(user):
    """Ajouter un nouveau client (auth requis)."""

    name = click.prompt("Nom du client")
    email = prompt_until_valid("Email", check_email, "Email invalide")
    phone = prompt_until_valid("Téléphone", check_phone, "Téléphone invalide")
    company = prompt_until_valid("Entreprise", check_company, "Entreprise invalide")
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


# === Commande : Modifier un Client ===
@cli.command()
@require_auth
@require_role(["commercial"])
def update_client(user):
    """Modifier un client existant (commercial = uniquement les siens)"""
    session = SessionLocal()
    clients = session.query(Client).filter_by(sales_contact=user.get('name')).all()

    if not clients:
        click.echo("❌ Aucun client ne vous est assigné.")
        session.close()
        return

    click.echo("\n📋 Liste de vos clients :")
    for c in clients:
        click.echo(f"  ID: {c.id} | Nom: {c.name} | Email: {c.email} | Téléphone: {c.phone}")

    client_id = prompt_until_valid("ID du client à modifier", check_number, "ID invalide")
    client = session.query(Client).filter_by(id=client_id, sales_contact=user.get('name')).first()

    if not client:
        click.echo("❌ Client introuvable ou non autorisé.")
        session.close()
        return

    click.echo(f"\n🔧 Modification du client : {client.name}")
    new_name = click.prompt("Nom", default=client.name, show_default=True)
    new_email = prompt_until_valid("Email", check_email, "Email invalide")
    new_phone = prompt_until_valid("Téléphone", check_phone, "Téléphone invalide")
    new_company = prompt_until_valid("Entreprise", check_company, "Entreprise invalide")

    client.name = new_name
    client.email = new_email
    client.phone = new_phone
    client.company = new_company
    client.last_updated = datetime.utcnow()

    session.commit()
    click.echo(f"✅ Client mis à jour : {client.name}")
    session.close()


# === Commande : Créer un Contrat ===
@cli.command()
@require_auth
@require_role(["gestion"])
def add_contract(user):
    """Ajouter un contrat pour un client existant"""
    session = SessionLocal()
    clients = session.query(Client).all()
    click.echo("\n=== Clients ===")
    for c in clients:
        click.echo(f"- {c.id}: {c.name} ({c.email})")

    client_id = prompt_until_valid("ID du client", check_number, "ID invalide")
    amount_total = prompt_until_valid("Montant total", check_amount, "Montant invalide")
    amount_remaining = prompt_until_valid("Montant restant", check_amount, "Montant invalide")
    status = prompt_until_valid("Statut (ex: signed, pending)", check_status, "Statut invalide")

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

    contract_id = prompt_until_valid("ID du contrat à modifier", check_number, "ID invalide")

    contract = session.get(Contract, contract_id)
    if not contract:
        click.echo("❌ Contrat non trouvé")
        return

    # Pour les commerciaux, vérifier qu'ils ne modifient que leurs contrats
    if user_role == "commercial" and contract.sales_contact != user.get('name'):
        click.echo("❌ Vous ne pouvez modifier que vos propres contrats.")
        return

    VALID_STATUSES = ["new", "pending", "signed", "cancelled"]
    click.echo(f"📌 Statuts disponibles : {', '.join(VALID_STATUSES)}")
    click.echo(f"🔎 Contrat actuel : {contract}")
    new_amount_total = prompt_until_valid("Nouveau montant total", check_amount, "Montant invalide")
    new_amount_remaining = prompt_until_valid("Nouveau montant restant", check_amount, "Montant invalide")

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


# === Commande : Afficher contrats non signés ou non payés ===
@cli.command()
@require_auth
@require_role(["commercial"])
def list_contracts_unsigned_unpaid(user):
    """Afficher les contrats qui ne sont pas signés ou pas payés"""
    session = SessionLocal()

    # Récupérer les contrats du commercial qui ne sont pas signés OU pas payés
    contracts = session.query(Contract).filter(
        Contract.sales_contact == user.get("name"),
        or_(
            Contract.status != "signed",
            Contract.amount_remaining > 0
        )
    ).all()

    if not contracts:
        click.echo("❌ Aucun contrat non signé ou non payé trouvé pour vous.")
        session.close()
        return

    click.echo("\n📄 Contrats non signés ou non payés :")
    for c in contracts:
        click.echo(
            f"  ID: {c.id} | Client: {c.client.name} | Montant: {c.amount_total} € | "
            f"Restant: {c.amount_remaining} € | Statut: {c.status}"
        )

    session.close()


# === Commande : Créer un Événement ===
@cli.command()
@require_auth
@require_role(["commercial"])
def add_event(user):
    """Ajouter un événement pour un contrat existant"""
    session = SessionLocal()

    # Récupérer les contrats signés du commercial
    contracts = session.query(Contract).filter_by(
        status="signed", sales_contact=user.get("name")
    ).all()

    if not contracts:
        click.echo("❌ Aucun contrat signé trouvé pour vous.")
        session.close()
        return

    click.echo("\n📄 Contrats signés disponibles :")
    for c in contracts:
        click.echo(f"  ID: {c.id} | Client: {c.client.name} | Montant: {c.amount_total} €")

    contract_id = prompt_until_valid("ID du contrat", check_number, "ID invalide")
    contract = session.query(Contract).filter_by(
        id=contract_id, status="signed", sales_contact=user.get("name")
    ).first()

    if not contract:
        click.echo("❌ Contrat introuvable ou non autorisé.")
        session.close()
        return

    support_users = session.query(User).join(Role).filter(Role.name == "support").all()

    if not support_users:
        click.echo("❌ Aucun utilisateur avec le rôle 'support' trouvé.")
        session.close()
        return

    click.echo("\n🧑‍💻 Contacts support disponibles :")
    for su in support_users:
        click.echo(f"  ID: {su.id} | Nom: {su.name} | Email: {su.email}")

    support_contact_input = click.prompt("ID du contact support", default="", show_default=False)

    if support_contact_input.strip() == "":
        support_contact_name = None
    else:
        try:
            support_contact_id = int(support_contact_input)
            support_user = next((u for u in support_users if u.id == support_contact_id), None)
            if not support_user:
                click.echo("❌ Contact support invalide.")
                session.close()
                return
            support_contact_name = support_user.name
        except ValueError:
            click.echo("❌ Veuillez entrer un identifiant valide ou laisser vide.")
            session.close()
            return

    start_days = prompt_until_valid("Jours à partir d'aujourd'hui pour START", check_number, "Nombre invalide")
    end_days = prompt_until_valid("Jours à partir d'aujourd'hui pour END", check_number, "Nombre invalide")
    location = click.prompt("Lieu")
    attendees = prompt_until_valid("Nombre de participants", check_number, "Nombre invalide")
    notes = click.prompt("Notes")

    client = contract.client
    event = Event(
        contract_id=contract.id,
        client_name=client.name,
        client_contact=f"{client.phone} | {client.email}",
        event_date_start=datetime.utcnow() + timedelta(days=start_days),
        event_date_end=datetime.utcnow() + timedelta(days=end_days),
        support_contact=support_contact_name,
        location=location,
        attendees=attendees,
        notes=notes
    )

    session.add(event)
    session.commit()
    click.echo(f"✅ Événement créé : {event}")
    session.close()


# === Commande : Modifier un Événement ===
@cli.command()
@require_auth
@require_role(["gestion", "support"])
def update_event(user):
    """Modifier un événement existant"""
    session = SessionLocal()
    user_role = user.get('role')

    if user_role == "gestion":
        events = session.query(Event).all()
    elif user_role == "support":
        events = session.query(Event).filter_by(support_contact=user.get('name')).all()
    else:
        click.echo("❌ Vous n'avez pas les droits pour modifier les événements.")
        return

    if not events:
        click.echo("❌ Aucun événement trouvé.")
        return

    click.echo("\n📅 Liste des événements :")
    for e in events:
        click.echo(f"  ID: {e.id} | Client: {e.client_name} | Lieu: {e.location}")

    event_id = prompt_until_valid("ID de l'événement à modifier", check_number, "ID invalide")
    event = session.get(Event, event_id)
    if not event:
        click.echo("❌ Événement non trouvé.")
        return
    # Pour le support, vérifier qu'ils ne modifient que leurs evenements
    if user_role == "support" and event.support_contact != user.get('name'):
        click.echo("⛔️ Vous ne pouvez modifier que les événements où vous êtes le contact support.")
        return

    start_days = click.prompt("Jours à partir d'aujourd'hui nouvelle date de début", default="", show_default=False)
    end_days = click.prompt("Jours à partir d'aujourd'hui nouvelle date de fin", default="", show_default=False)
    new_start_days = int(start_days) if start_days.strip().isdigit() else None
    new_end_days = int(end_days) if end_days.strip().isdigit() else None
    new_support = click.prompt("Nouveau contact support", default=event.support_contact, show_default=True)
    new_location = click.prompt("Nouveau lieu", default=event.location, show_default=True)
    new_attendees = prompt_until_valid("Nouveau nombre de participants", check_number, "Nombre invalide")
    new_notes = click.prompt("Nouvelles notes", default=event.notes, show_default=True)

    if new_start_days is not None:
        event.event_date_start = datetime.utcnow() + timedelta(days=new_start_days)
    if new_end_days is not None:
        event.event_date_end = datetime.utcnow() + timedelta(days=new_end_days)

    event.support_contact = new_support
    event.location = new_location
    event.attendees = new_attendees
    event.notes = new_notes

    session.commit()
    click.echo(f"✅ Événement modifié : {event}")
    session.close()


# === Commande : Afficher Événements sans support ===
@cli.command()
@require_role(["gestion"])
def list_events_no_support():
    """Lister les évènements sans support"""
    session = SessionLocal()
    events = session.query(Event).filter(Event.support_contact.is_(None)).all()

    if not events:
        click.echo("✅ Tous les événements ont un support assigné.")
    else:
        click.echo("\n📅 Événements sans support :")
        for e in events:
            click.echo(f"- ID: {e.id} | Client: {e.client_name} | Début: {e.event_date_start} | Lieu: {e.location}")

    session.close()


# === Commande : Afficher Événements pour support ===
@cli.command()
@require_auth
@require_role(["support"])
def list_events_support(user):
    """Lister les évènements assignés à l'utilisateur support"""
    session = SessionLocal()
    events = session.query(Event).filter_by(support_contact=user.get('name')).all()

    if not events:
        click.echo("❌ Aucun événement trouvé pour vous.")
        session.close()
        return

    click.echo("\n📅 Liste des événements où vous êtes contact support :")
    for e in events:
        click.echo(f"  ID: {e.id} | Client: {e.client_name} | Lieu: {e.location} | Début: {e.event_date_start}")

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
