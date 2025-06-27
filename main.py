import questionary
from crm.cli import add_user, delete_user, update_user, list_users
from crm.cli import add_event, update_event, list_events_no_support, list_events_support
from crm.cli import add_client, update_client
from crm.cli import add_contract, update_contract, list_contracts_unsigned_unpaid
from crm.cli import add_role, login, logout, whoami
import sys


def menu_admin():
    while True:
        choix = questionary.select(
            "Actions Admin:",
            choices=[
                "Ajouter un role",
                "Se connecter",
                "Se déconnecter",
                "Qui est connecté ?",
                "Retour au menu principal",
                "Quitter"
            ]).ask()

        if choix == "Ajouter un role":
            add_role()
        elif choix == "Se connecter":
            login()
        elif choix == "Se déconnecter":
            logout()
        elif choix == "Qui est connecté ?":
            whoami()
        elif choix == "Retour au menu principal":
            break
        elif choix == "Quitter":
            print("Au revoir!")
            sys.exit(0)


def menu_users():
    while True:
        choix = questionary.select(
            "Actions Utilisateurs:",
            choices=[
                "Ajouter un utilisateur",
                "Supprimer un utilisateur",
                "Modifier un utilisateur",
                "Lister les utilisateurs",
                "Retour au menu principal",
                "Quitter"
            ]).ask()

        if choix == "Ajouter un utilisateur":
            add_user()
        elif choix == "Supprimer un utilisateur":
            try:
                delete_user()
            except SystemExit:
                print("Action terminée, retour au menu.")
            except Exception as e:
                print(f"Erreur inattendue : {e}")
        elif choix == "Modifier un utilisateur":
            update_user()
        elif choix == "Lister les utilisateurs":
            list_users()
        else:
            print("Au revoir!")
            break


def menu_events():
    while True:
        choix = questionary.select(
            "Actions Événements:",
            choices=[
                "Ajouter un événement",
                "Modifier un événement",
                "Afficher événements sans support",
                "Afficher événements pour support",
                "Retour au menu principal",
                "Quitter"
            ]).ask()

        if choix == "Ajouter un événement":
            add_event()
        elif choix == "Modifier un événement":
            update_event()
        elif choix == "Afficher événements sans support":
            list_events_no_support()
        elif choix == "Afficher événements pour support":
            list_events_support()
        elif choix == "Retour au menu principal":
            break
        elif choix == "Quitter":
            print("Au revoir!")
            sys.exit(0)


def menu_clients():
    while True:
        choix = questionary.select(
            "Actions Clients:",
            choices=[
                "Ajouter un client",
                "Modifier un client",
                "Retour au menu principal",
                "Quitter"
            ]).ask()

        if choix == "Ajouter un client":
            add_client()
        elif choix == "Modifier un client":
            update_client()
        elif choix == "Retour au menu principal":
            break
        elif choix == "Quitter":
            print("Au revoir!")
            sys.exit(0)


def menu_contracts():
    while True:
        choix = questionary.select(
            "Actions Contrats:",
            choices=[
                "Ajouter un contrat",
                "Modifier un contrat",
                "Afficher contrats non signés ou non payés",
                "Retour au menu principal",
                "Quitter"
            ]).ask()

        if choix == "Ajouter un contrat":
            add_contract()
        elif choix == "Modifier un contrat":
            update_contract()
        elif choix == "Afficher contrats non signés ou non payés":
            list_contracts_unsigned_unpaid()
        elif choix == "Retour au menu principal":
            break
        elif choix == "Quitter":
            print("Au revoir!")
            sys.exit(0)


def main():
    while True:
        choix = questionary.select(
            "Que voulez-vous gérer ?",
            choices=[
                "Admin",
                "Utilisateurs",
                "Événements",
                "Clients",
                "Contrats",
                "Quitter"
            ]).ask()

        if choix == "Utilisateurs":
            menu_users()
        elif choix == "Événements":
            menu_events()
        elif choix == "Clients":
            menu_clients()
        elif choix == "Contrats":
            menu_contracts()
        elif choix == "Admin":
            menu_admin()
        elif choix == "Retour au menu principal":
            break
        elif choix == "Quitter":
            print("Au revoir!")
            sys.exit(0)


if __name__ == "__main__":
    main()
