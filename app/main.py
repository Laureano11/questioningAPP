import datetime

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
# Archivos mios

from .database import create_db_and_tables, get_session
from .models import User, Question


# 1. Lifespan: Esto se ejecuta justo antes de que la app empiece a recibir visitas
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables() # Crea el archivo database.db y las tablas
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="secreto-super-seguro")
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


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



@app.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    # Inyectamos la sesión de base de datos
    session: Session = Depends(get_session)
):
    new_user= User(username=username, email=email, password=password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    request.session["user_id"] = new_user.id
    request.session["username"] = new_user.username
    return RedirectResponse(url="/",status_code=303)



@app.get("/question", response_class=HTMLResponse)
async def question(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse("question.html", {"request": request})

@app.post("/question")
async def question(
    request: Request,
    content: str = Form(...),
    # Inyectamos la sesión de base de datos
    session: Session = Depends(get_session)
):
    new_question= Question(content=content)
    session.add(new_question)
    session.commit()
    session.refresh(question)
    return RedirectResponse(url="/",status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# --- RUTA POST: Procesar el Login ---
@app.post("/login", response_class=HTMLResponse)
async def login_logic(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        session: Session = Depends(get_session)  # Tu conexión a BD
):
    # 1. BUSCAR USUARIO EN LA BD
    # "Select * From User Where username = ... limit 1"
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()

    # 2. VALIDAR
    # ¿Existe el usuario? ¿La contraseña coincide?
    if not user or user.password != password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos"  # Feedback visual
        })

    # 3. CREAR LA SESIÓN (Darle la pulsera)
    # Guardamos el ID y el nombre en la cookie encriptada
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    return RedirectResponse(url="/", status_code=303)


# --- RUTA LOGOUT: Salir ---
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # Romper la pulsera
    return RedirectResponse(url="/", status_code=303)
