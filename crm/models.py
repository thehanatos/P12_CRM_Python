from .database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from argon2 import PasswordHasher


ph = PasswordHasher()


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # ex: commercial, support, gestion

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(name={self.name})>"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    employee_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="users")

    def set_password(self, password: str):
        self.hashed_password = ph.hash(password)

    def verify_password(self, password: str) -> bool:
        try:
            return ph.verify(self.hashed_password, password)
        except Exception:
            return False

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email}, role={self.role.name})>"


# === Client ===
class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)
    company = Column(String)
    created_at = Column(DateTime)
    last_updated = Column(DateTime)

    # Contact commercial
    sales_contact = Column(String, nullable=True)
    # Relations
    contracts = relationship("Contract", back_populates="client")
    # lien vers le User qui a créé le client
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User")

    def __repr__(self):
        return f"<Client(name={self.name}, sales_contact={self.sales_contact})>"


# === Contract ===
class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)

    # Identifiant unique lisible
    unique_id = Column(String, unique=True, nullable=False)

    # Foreign Key vers Client
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    client = relationship("Client", back_populates="contracts")

    # Contact commercial pour le contrat (copié du client, mais stocké à part pour historique)
    sales_contact = Column(String, nullable=True)

    amount_total = Column(Float, nullable=False)
    amount_remaining = Column(Float, nullable=False)
    created_at = Column(DateTime)
    status = Column(String)  # ex: "signed", "pending"

    # Relation vers Event
    events = relationship("Event", back_populates="contract")

    def __repr__(self):
        return f"<Contract(unique_id={self.unique_id}, amount_total={self.amount_total})>"


# === Event ===
class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)

    # Foreign Key vers Contract
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    contract = relationship("Contract", back_populates="events")

    client_name = Column(String, nullable=False)

    # Contact client : phone + email concaténés
    client_contact = Column(String, nullable=True)

    event_date_start = Column(DateTime, nullable=False)
    event_date_end = Column(DateTime, nullable=False)

    # Support contact
    support_contact = Column(String, nullable=True)

    location = Column(String, nullable=True)
    attendees = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    def __repr__(self):
        return f"<Event(client_name={self.client_name}, date_start={self.event_date_start})>"
