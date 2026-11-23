"""Punto de entrada de la aplicación.

Ejecutar:  uvicorn app.main:app --reload
"""
import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware

from app.database import init_db
from app.routers import api, web
from app.services.errores import ErrorNegocio

log = logging.getLogger("licitaciones")


def crear_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app):
        init_db()
        yield

    app = FastAPI(title="Sistema de Gestión de Licitaciones", debug=False, lifespan=lifespan)

    # La clave de sesión viene de una variable de entorno; si falta se genera
    # una aleatoria (las sesiones se pierden al reiniciar, los datos no).
    clave = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    app.add_middleware(SessionMiddleware, secret_key=clave, same_site="lax", https_only=False)

    app.include_router(api.router)
    app.include_router(web.router)

    # ---------- Manejo controlado de errores (REQ-012) ----------
    @app.exception_handler(ErrorNegocio)
    async def _negocio(request: Request, exc: ErrorNegocio):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.mensaje})

    @app.exception_handler(RequestValidationError)
    async def _validacion(request: Request, exc: RequestValidationError):
        campos = sorted({str(e["loc"][-1]) for e in exc.errors()})
        return JSONResponse(status_code=422, content={"error": "Datos inválidos.", "campos": campos})

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})

    @app.exception_handler(Exception)
    async def _interno(request: Request, exc: Exception):
        # Se registra en el log del servidor, pero al cliente no se le muestra la traza.
        log.exception("Error interno en %s %s", request.method, request.url.path)
        if request.url.path.startswith("/api"):
            return JSONResponse(status_code=500, content={"error": "Error interno. Intente de nuevo más tarde."})
        return PlainTextResponse("Ocurrió un error interno. Intente de nuevo más tarde.", status_code=500)

    return app


app = crear_app()
