from sqlalchemy import create_engine, text
from models import Base
import getpass

password = getpass.getpass("Mot de passe PostgreSQL : ")

# Format : postgresql://<user>:<password>@<host>/<dbname>
DATABASE_URL = f"postgresql://mon_superuser:{password}@localhost/crm_python"

if not DATABASE_URL:
    raise ValueError("DATABASE_URL n'est pas définie !")

engine = create_engine(DATABASE_URL)

# === Étape 1 : Créer les tables ===
print("✅ Création des tables...")
Base.metadata.create_all(engine)
print("✅ Tables créées avec succès.")

# === Étape 2 : Vérifier la connexion ===
with engine.connect() as connection:
    result = connection.execute(text("SELECT version();"))
    print("✅ Connexion OK, version PostgreSQL :", result.scalar())

# === Étape 3 : Vérifier les tables ===
with engine.connect() as connection:
    result = connection.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public';"
    ))
    tables = result.fetchall()
    print("✅ Tables présentes dans la base :", [t[0] for t in tables])
