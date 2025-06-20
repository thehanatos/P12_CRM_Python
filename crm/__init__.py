# crm/__init__.py

from .database import Base, engine, SessionLocal
from .models import Client, Contract, Event, User, Role
from .auth import (
    authenticate_user,
    save_token,
    load_token,
    decode_token,
    get_current_user,
    require_role,
)

__all__ = [
    "Base", "engine", "SessionLocal",
    "Client", "Contract", "Event", "User", "Role",
    "authenticate_user", "save_token", "load_token",
    "decode_token", "get_current_user", "require_role",
]
