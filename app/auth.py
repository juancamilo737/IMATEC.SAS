"""Autenticación por cookie firmada. Sin dependencias externas."""
import base64, hashlib, hmac, json, secrets, time
from fastapi import Request
from .config import SECRET_KEY, SESSION_COOKIE, SESSION_MAX_AGE
from . import db

_ITER = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(it))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _sign(data: bytes) -> str:
    sig = hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data).decode().rstrip("=") + "." + \
           base64.urlsafe_b64encode(sig).decode().rstrip("=")


def _unsign(token: str):
    try:
        raw, sig = token.split(".")
        data = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        got = base64.urlsafe_b64decode(sig + "=" * (-len(sig) % 4))
        exp = hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).digest()
        if not hmac.compare_digest(got, exp):
            return None
        return json.loads(data)
    except Exception:
        return None


def make_session(user: dict) -> str:
    payload = {"uid": user["id"], "rol": user["rol"], "nombre": user["nombre"],
               "email": user["email"], "cliente_id": user.get("cliente_id"),
               "exp": int(time.time()) + SESSION_MAX_AGE}
    return _sign(json.dumps(payload).encode())


def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    data = _unsign(token)
    if not data or data.get("exp", 0) < time.time():
        return None
    return data


def autenticar(email: str, password: str):
    u = db.q1("SELECT * FROM usuarios WHERE lower(email)=lower(?) AND activo=1", (email.strip(),))
    if not u or not verify_password(password, u["password_hash"]):
        return None
    db.ex("UPDATE usuarios SET ultimo_acceso=datetime('now','localtime') WHERE id=?", (u["id"],))
    return u


def crear_usuario(email, password, nombre, rol="cliente", cliente_id=None) -> int:
    return db.ex(
        "INSERT INTO usuarios(email,password_hash,nombre,rol,cliente_id) VALUES(?,?,?,?,?)",
        (email.strip().lower(), hash_password(password), nombre, rol, cliente_id))


def es_staff(user) -> bool:
    return bool(user) and user.get("rol") in ("admin", "vendedor")
