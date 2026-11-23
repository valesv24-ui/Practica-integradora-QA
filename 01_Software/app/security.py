"""Autenticación: hash de contraseñas y control de sesión."""
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario

_ITERACIONES = 200_000


def hash_password(password: str) -> str:
    sal = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${sal.hex()}${dk.hex()}"


def verificar_password(password: str, guardado: str) -> bool:
    try:
        _, iteraciones, sal_hex, dk_hex = guardado.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk.hex(), dk_hex)


def autenticar(db: Session, usuario: str, password: str) -> Usuario | None:
    u = db.query(Usuario).filter(Usuario.usuario == usuario.strip()).first()
    if u and verificar_password(password, u.password_hash):
        return u
    return None


def crear_usuario(db: Session, usuario: str, password: str) -> Usuario:
    u = Usuario(usuario=usuario.strip(), password_hash=hash_password(password))
    db.add(u)
    db.commit()
    return u


def usuario_actual(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Dependencia para la API: responde 401 si no hay sesión."""
    uid = request.session.get("uid")
    u = db.get(Usuario, uid) if uid else None
    if u is None:
        raise HTTPException(status_code=401, detail="Debe iniciar sesión.")
    return u
