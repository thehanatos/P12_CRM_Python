from crm.database import SessionLocal
from crm.models import User, Client, Role, Event, Contract

session = SessionLocal()

try:
    deleted_events = session.query(Event).filter(Event.id > 1000).delete(synchronize_session=False)
    deleted_contracts = session.query(Contract).filter(Contract.id > 1000).delete(synchronize_session=False)
    deleted_users = session.query(User).filter(User.id > 1000).delete(synchronize_session=False)
    deleted_clients = session.query(Client).filter(Client.id > 1000).delete(synchronize_session=False)
    deleted_roles = session.query(Role).filter(Role.id > 3).delete(synchronize_session=False)

    session.commit()

    print(f"✅ Nettoyage effectué :\n"
          f"  - {deleted_contracts} contrats supprimés\n"
          f"  - {deleted_events} événements supprimés\n"
          f"  - {deleted_users} utilisateurs supprimés\n"
          f"  - {deleted_clients} clients supprimés\n"
          f"  - {deleted_roles} rôles supprimés")

except Exception as e:
    session.rollback()
    print(f"❌ Erreur pendant la suppression : {e}")

finally:
    session.close()
