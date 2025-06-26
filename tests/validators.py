import re


def check_email(email: str) -> bool:
    """Vérifie si l'email est valide"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def check_phone(phone: str) -> bool:
    """Vérifie si le téléphone contient uniquement des chiffres ou des tirets"""
    pattern = r'^[\d\-]+$'
    return re.match(pattern, phone) is not None


def check_name(name: str) -> bool:
    """Le nom doit contenir uniquement des lettres et éventuellement des espaces"""
    pattern = r'^[A-Za-zÀ-ÿ\s\-]+$'
    return re.match(pattern, name) is not None


def check_company(company: str) -> bool:
    """La compagnie doit être une chaîne non vide"""
    return isinstance(company, str) and bool(company.strip())


def check_amount(amount) -> bool:
    """Vérifie si la valeur est un nombre (int ou float)"""
    try:
        float(amount)
        return True
    except ValueError:
        return False


def check_role(role: str) -> bool:
    """Vérifie si le rôle est valide"""
    return role.lower() in ["commercial", "support", "gestion"]


def check_number(value: str) -> bool:
    """Vérifie que la valeur contient uniquement des chiffres"""
    return value.isdigit()


def check_status(status: str) -> bool:
    """Vérifie si le status est parmi les valeurs autorisées"""
    return status.lower() in ["new", "pending", "signed", "cancelled"]
