import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from crm.cli import generate_next_employee_number, prompt_until_valid
from crm.models import Base, User, Role, Client, Contract, Event
from crm.database import SessionLocal
from tests.validators import check_email, check_phone, check_role, check_company
from tests.validators import check_number, check_amount, check_status
import sys
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from crm import cli
import uuid

# Ajoute le dossier parent (racine du projet) au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["SKIP_AUTH_FOR_TESTS"] = "1"


# Configuration base de test en mémoire
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


def get_or_create_role(session, name):
    role = session.query(Role).filter_by(name=name).first()
    if not role:
        role = Role(name=name)
        session.add(role)
        session.commit()
    return role


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    role = Role(name="test")
    session.add(role)
    session.commit()

    yield session  # Exécute les tests

    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_generate_next_employee_number_empty(db_session):
    result = generate_next_employee_number(db_session)
    assert result == "EMP001"


def test_check_email_valid():
    assert check_email("test@example.com")
    assert not check_email("invalid-email")


def test_check_phone_valid():
    assert check_phone("0612345678")
    assert not check_phone("abcd123")


def test_check_role_valid():
    assert check_role("gestion")
    assert check_role("support")
    assert not check_role("admin")


def test_check_company_valid():
    assert check_company("ACME")
    assert not check_company("")


def test_check_number_valid():
    assert check_number("42")
    assert not check_number("abc")


def test_check_amount_valid():
    assert check_amount("1000")
    assert not check_amount("one hundred")


def test_check_status_valid():
    assert check_status("signed")
    assert not check_status("closed")


def test_event_dates_logic(db_session):
    client = Client(
        name="Test Client",
        email="client@example.com",
        phone="0123456789",
        company="ACME",
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        sales_contact="Test User"
    )
    db_session.add(client)
    db_session.commit()

    contract = Contract(
        unique_id="uuid-1234",
        client_id=client.id,
        sales_contact=client.sales_contact,
        amount_total=1000,
        amount_remaining=200,
        created_at=datetime.utcnow(),
        status="signed"
    )
    db_session.add(contract)
    db_session.commit()

    event = Event(
        contract_id=contract.id,
        client_name=client.name,
        client_contact=f"{client.phone} | {client.email}",
        event_date_start=datetime.utcnow() + timedelta(days=2),
        event_date_end=datetime.utcnow() + timedelta(days=5),
        support_contact="Support Guy",
        location="Paris",
        attendees=50,
        notes="Test Event"
    )
    db_session.add(event)
    db_session.commit()

    assert event.event_date_end > event.event_date_start
    assert event.attendees == 50
    assert event.contract_id == contract.id


def test_prompt_until_valid_mock(monkeypatch):
    inputs = iter(["bad input", "test@example.com"])

    monkeypatch.setattr("click.prompt", lambda *args, **kwargs: next(inputs))
    monkeypatch.setattr("click.echo", lambda x: None)  # Supprime l'affichage

    result = prompt_until_valid("Email", check_email)
    assert result == "test@example.com"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def session_mock(monkeypatch):
    mock_session = MagicMock()
    monkeypatch.setattr(cli, "SessionLocal", lambda: mock_session)
    return mock_session


def test_add_role(runner, session_mock):
    session = session_mock
    with patch("crm.cli.prompt_until_valid", return_value="gestion"):
        result = runner.invoke(cli.add_role)
    assert "✅ Rôle créé" in result.output
    session.add.assert_called()
    session.commit.assert_called()
    session.close.assert_called()


def test_add_user_success(runner, session_mock):
    session = session_mock
    mock_role = MagicMock()
    mock_role.name = "gestion"
    session.query.return_value.filter_by.return_value.first.return_value = mock_role
    session.query.return_value.all.return_value = []

    with patch("crm.cli.generate_next_employee_number", return_value="001"), \
         patch("crm.cli.prompt_until_valid", side_effect=["test@example.com", "gestion"]), \
         patch("crm.cli.click.prompt", side_effect=["Test User", "pass", "pass"]):
        result = runner.invoke(cli.add_user)

    assert "✅ Utilisateur créé" in result.output
    session.add.assert_called()
    session.commit.assert_called()


def test_update_user_user_not_found(runner, session_mock):
    session = session_mock
    session.query.return_value.all.return_value = []
    session.get.return_value = None

    with patch("crm.cli.prompt_until_valid", return_value="1"):
        result = runner.invoke(cli.update_user)
    assert "❌ Utilisateur non trouvé" in result.output


def test_delete_user_cancel(runner, session_mock):
    session = session_mock
    mock_user = MagicMock()
    mock_user.name = "John Doe"
    session.query.return_value.all.return_value = [mock_user]
    session.get.return_value = mock_user

    with patch("crm.cli.prompt_until_valid", return_value="1"), \
         patch("crm.cli.click.confirm", return_value=False):
        result = runner.invoke(cli.delete_user)

    assert "❌ Suppression annulée." in result.output
    session.delete.assert_not_called()


def test_list_events_no_support(runner, monkeypatch):
    session = SessionLocal()
    role = session.query(Role).filter_by(name="support").first()
    if not role:
        role = Role(name="support")
        session.add(role)
        session.commit()

    user = User(name="Support Guy", email=f"support+{uuid.uuid4()}@example.com",
                employee_number=f"{uuid.uuid4()}", role=role)
    user.set_password("password123")
    session.add(user)
    session.commit()

    result = runner.invoke(cli.list_events_no_support, obj={"role": "support"})

    assert "✅ Les événements ont un support assigné." in result.output or "Événements sans support" in result.output

    session.delete(user)
    session.commit()
    session.close()


def test_list_users_only_for_gestion(runner, session_mock):
    session = session_mock
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.name = "Admin"
    mock_user.email = "admin@test.com"
    mock_user.role.name = "gestion"
    session.query.return_value.all.return_value = [mock_user]

    result = runner.invoke(cli.list_users)
    assert "Admin (admin@test.com)" in result.output


def test_list_all(runner, monkeypatch):
    session = SessionLocal()

    # Création des données
    client = Client(
        name="Client Test",
        email=f"client+{uuid.uuid4()}@example.com",
        phone="0102030405",
        company="TestCorp"
    )
    session.add(client)
    session.commit()

    contract = Contract(
        client_id=client.id,
        sales_contact="SalesUser",
        amount_total=2000,
        amount_remaining=500,
        status="signed",
        unique_id=str(uuid.uuid4())
    )
    session.add(contract)
    session.commit()

    event = Event(
        client_name=client.name,
        contract_id=contract.id,
        client_contact=client.phone,
        support_contact="Support Guy",
        event_date_start=datetime.utcnow(),
        event_date_end=datetime.utcnow() + timedelta(days=1),
        location="Lyon",
        attendees=50,
        notes="Note test"
    )
    session.add(event)
    session.commit()

    # Exécution de la commande CLI
    result = runner.invoke(cli.list_all)

    # Vérifications dans la sortie
    assert "=== Clients ===" in result.output
    assert client.name in result.output
    assert client.email in result.output

    assert "=== Contrats ===" in result.output
    assert contract.unique_id in result.output
    assert str(contract.amount_total) in result.output

    assert "=== Événements ===" in result.output
    assert event.client_name in result.output
    assert event.location in result.output

    # Nettoyage
    session.delete(event)
    session.delete(contract)
    session.delete(client)
    session.commit()
    session.close()
