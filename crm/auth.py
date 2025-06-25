import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from argon2 import PasswordHasher
from crm.database import SessionLocal
from crm.models import User
from sqlalchemy.orm import joinedload
import functools
import click

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 60))

ph = PasswordHasher()
TOKEN_FILE = ".token"


def authenticate_user(email: str, password: str):
    """Authentifie l'utilisateur et génère un token JWT"""
    session = SessionLocal()
    user = session.query(User).options(joinedload(User.role)).filter_by(email=email).first()

    if not user:
        session.close()
        raise click.ClickException("❌ Utilisateur non trouvé")

    try:
        ph.verify(user.hashed_password, password)
    except Exception:
        session.close()
        raise click.ClickException("❌ Mot de passe incorrect")

    payload = {
        "sub": str(user.id),
        "name": user.name,
        "role": user.role.name if user.role else None,
        "department": user.role.name if user.role else None,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }

    session.close()

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    save_token(token)
    return token


def save_token(token: str):
    """Sauvegarde le token JWT localement"""
    with open(TOKEN_FILE, "w") as f:
        f.write(token)


def load_token() -> str:
    """Charge le token JWT localement"""
    print("🔍 Chargement du token...")
    if not os.path.exists(TOKEN_FILE):
        raise click.ClickException("🔑 Aucun token trouvé. Connectez-vous avec `login`.")
    with open(TOKEN_FILE, "r") as f:
        return f.read().strip()


def decode_token(token: str):
    """Vérifie et décode le token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise click.ClickException("⏰ Token expiré. Veuillez vous reconnecter.")
    except jwt.InvalidTokenError:
        raise click.ClickException("🔐 Token invalide. Veuillez vous reconnecter.")


def get_current_user():
    """Retourne les infos de l'utilisateur connecté"""
    token = load_token()
    payload = decode_token(token)
    return payload


def require_role(required_roles):
    """Décorateur pour vérifier le rôle"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user['role'] not in required_roles:
                raise click.ClickException(f"⛔ Accès refusé pour le rôle : {user['role']}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(f):
    """Décorateur qui force l’authentification avant d’exécuter la fonction."""
    import functools

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()  # lève une exception si pas connecté
        return f(user, *args, **kwargs)
    return wrapper
