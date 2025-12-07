import datetime
from typing import Optional, List

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from .routers import auth, questions
# Archivos mios

from .database import create_db_and_tables, get_session
from .models import User, Question, Answer

# 1. Lifespan: Esto se ejecuta justo antes de que la app empiece a recibir visitas
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables() # Crea el archivo database.db y las tablas
    yield



app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(questions.router)
# EJEMPLO: Que la sesión expire en 1 hora (3600 segundos)
app.add_middleware(
    SessionMiddleware,
    secret_key="secreto-super-seguro",
    max_age=600# <--- ESTA ES LA LÍNEA MÁGICA
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session: Session = Depends(get_session)):
    # CONSULTA SQL: "Dame todos los usuarios"
    statement = select(User)
    users = session.exec(statement).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "usuarios": users  # Pasamos la lista REAL de objetos a la plantilla
    })

def validar_usuario(request: Request):
    username = request.session.get("username")
    if username is None:
        return "Anonimo"
    else:
        return username