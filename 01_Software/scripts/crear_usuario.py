"""Crea un usuario para iniciar sesión.

Uso:  python -m scripts.crear_usuario <usuario>
La contraseña se pide por teclado (no queda en el historial ni en el repo).
"""
import getpass
import sys

from app.database import SessionLocal, init_db
from app.models import Usuario
from app.security import crear_usuario


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python -m scripts.crear_usuario <usuario>")
        sys.exit(1)
    nombre = sys.argv[1]
    password = getpass.getpass("Contraseña: ")
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)
    if password != getpass.getpass("Repita la contraseña: "):
        print("Las contraseñas no coinciden.")
        sys.exit(1)

    init_db()
    db = SessionLocal()
    try:
        if db.query(Usuario).filter(Usuario.usuario == nombre).first():
            print(f"El usuario «{nombre}» ya existe.")
            sys.exit(1)
        crear_usuario(db, nombre, password)
        print(f"Usuario «{nombre}» creado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
