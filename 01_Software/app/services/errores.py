"""Errores de negocio. Cada uno se traduce a un código HTTP controlado."""


class ErrorNegocio(Exception):
    status_code = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ReglaNegocio(ErrorNegocio):
    """Dato inválido según una regla (monto, nombre, plazo...)."""
    status_code = 422


class Conflicto(ErrorNegocio):
    """Duplicado o estado incompatible."""
    status_code = 409


class NoEncontrado(ErrorNegocio):
    status_code = 404
