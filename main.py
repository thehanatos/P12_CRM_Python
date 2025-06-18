from crm.database import engine

if __name__ == "__main__":
    with engine.connect() as connection:
        version = connection.execute("SELECT version();").scalar()
        print(f"✅Connexion OK : PostgreSQL version {version}")
