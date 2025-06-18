import os
import uuid
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Client, Contract, Event

# === Charger les variables d'environnement ===
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# === Créer le moteur et la session ===
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

# === Créer les tables si pas déjà créées ===
Base.metadata.create_all(engine)

# === 1) Créer un client ===
client = Client(
    name="Acme Corp",
    email="contact@acme.com",
    phone="123-456-7890",
    company="Acme Corporation",
    created_at=datetime.utcnow(),
    last_updated=datetime.utcnow(),
    sales_contact="John Doe"
)

session.add(client)
session.commit()  # Commit pour récupérer l'ID du client

print(f"✅ Client créé : {client}")

# === 2) Créer un contrat pour ce client ===
contract = Contract(
    unique_id=str(uuid.uuid4()),   # identifiant unique généré
    client_id=client.id,
    sales_contact=client.sales_contact,  # même commercial
    amount_total=10000.0,
    amount_remaining=4000.0,
    created_at=datetime.utcnow(),
    status="signed"
)

session.add(contract)
session.commit()

print(f"✅ Contrat créé : {contract}")

# === 3) Créer un événement pour ce contrat ===
event = Event(
    contract_id=contract.id,
    client_name=client.name,
    client_contact=f"{client.phone} | {client.email}",
    event_date_start=datetime.utcnow() + timedelta(days=30),
    event_date_end=datetime.utcnow() + timedelta(days=31),
    support_contact="Jane Smith",
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
