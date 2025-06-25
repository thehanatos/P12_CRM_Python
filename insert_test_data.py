import os
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from argon2 import PasswordHasher
from crm.models import Base, Client, Contract, Event, User, Role

# === Charger les variables d'environnement ===
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# === Créer le moteur et la session ===
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# === Créer les tables si pas déjà créées ===
# Base.metadata.drop_all(engine)   # Pour tout supprimer
Base.metadata.create_all(engine)

# === Préparer le hash de mot de passe ===
ph = PasswordHasher()

# === 1) Créer les rôles ===
role_sales = Role(name="commercial")
role_support = Role(name="support")
role_management = Role(name="gestion")

session.add_all([role_sales, role_support, role_management])
session.commit()

print("✅ Rôles créés")

# === 2) Créer des utilisateurs ===
users = [
    User(
        employee_number="EMP001",
        name="Alice Commercial",
        email="alice@crm.com",
        role=role_sales,
        hashed_password=ph.hash("passWord123456")
    ),
    User(
        employee_number="EMP002",
        name="Bob Support",
        email="bob@crm.com",
        role=role_support,
        hashed_password=ph.hash("passWord123456")
    ),
    User(
        employee_number="EMP003",
        name="Charlie Manager",
        email="charlie@crm.com",
        role=role_management,
        hashed_password=ph.hash("passWord123456")
    ),
]

session.add_all(users)
session.commit()

print("✅ Utilisateurs créés")

# === 3) Créer un client géré par un commercial ===
client = Client(
    name="Acme Corp",
    email="contact@acme.com",
    phone="123-456-7890",
    company="Acme Corporation",
    created_at=datetime.utcnow(),
    last_updated=datetime.utcnow(),
    sales_contact=users[0].name  # commercial Alice
)
session.add(client)
session.commit()

print(f"✅ Client créé : {client}")

# === 4) Créer un contrat ===
contract = Contract(
    unique_id=str(uuid.uuid4()),
    client_id=client.id,
    sales_contact=client.sales_contact,
    amount_total=10000.0,
    amount_remaining=4000.0,
    created_at=datetime.utcnow(),
    status="signed"
)
session.add(contract)
session.commit()

print(f"✅ Contrat créé : {contract}")

# === 5) Créer un événement ===
event = Event(
    contract_id=contract.id,
    client_name=client.name,
    client_contact=f"{client.phone} | {client.email}",
    event_date_start=datetime.utcnow() + timedelta(days=30),
    event_date_end=datetime.utcnow() + timedelta(days=31),
    support_contact=users[1].name,  # support Bob
    location="Acme HQ - Paris",
    attendees=50,
    notes="Prévoir projecteur et Wi-Fi."
)
session.add(event)
session.commit()

print(f"✅ Événement créé : {event}")

# === Fermer proprement ===
session.close()
print("🎉 Données de test insérées avec succès !")
