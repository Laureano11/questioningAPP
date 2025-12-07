import datetime
from typing import Optional, List

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
# Archivos mios

from .database import create_db_and_tables, get_session
from .models import User, Question, Answer


# 1. Lifespan: Esto se ejecuta justo antes de que la app empiece a recibir visitas
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables() # Crea el archivo database.db y las tablas
    yield

opciones=["Lauri", "Hipo","Choco", "Dama","Pato","Bauti", "Enzo", "Giampe", "Franza", "Rata", "Mateo" ]
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
    query = select(Question).order_by(Question.uploaded_at.desc())
    questions = session.exec(query).all()
    return templates.TemplateResponse("question.html", {"request": request,
                                                        "questions": questions})


@app.get("/question/{question_id}", response_class=HTMLResponse)
async def question_detail(
        request: Request,
        question_id: int,  # FastAPI extrae este número de la URL
        session: Session = Depends(get_session)
):
    # 1. Buscamos la pregunta por su ID y sus RTAS
    question = session.get(Question, question_id)
    query = select(Answer).where(Answer.question_id == question_id).order_by(Answer.uploaded_at.desc())
    answers = session.exec(query).all()
    # 2. Si no existe (alguien puso un ID falso en la URL), damos error 404
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    # 3. Renderizamos la nueva plantilla pasando el objeto 'question'
    return templates.TemplateResponse("questioninfo.html", {
        "request": request,
        "question": question,
        "answers": answers,
        "opciones": opciones
    })

@app.post("/question")
async def question(
    request: Request,
    content: str = Form(...),
    is_anonymous: Optional[str] = Form(None),
    session: Session = Depends(get_session)
    ):
    real_user = request.session.get("username")
    if is_anonymous:
        final_author = "Anónimo 👻"  # Puedes poner un emoji para distinguir
    else:
        # Si no está logueado y no puso anónimo, ponemos "Desconocido" o lo mandamos al login
        final_author = real_user if real_user else "Anonimo 👻"
    new_question= Question(content=content, uploaded_by=final_author, uploaded_at=datetime.datetime.now())
    session.add(new_question)
    session.commit()
    session.refresh(new_question)
    return RedirectResponse(url="/question",status_code=303)

@app.post("/question/{question_id}/answer")
async def question_answer(
    request: Request,
    question_id: int, #
    content: List[str] = Form(...),
    session: Session = Depends(get_session)
):
    content = ", ".join(content)
    username = validar_usuario(request)

    new_answer = Answer(content=content,
                        question_id=question_id,
                        uploaded_by=username)
    session.add(new_answer)
    session.commit()
    session.refresh(new_answer)
    return RedirectResponse(url=f"/question/{question_id}",status_code=303)

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
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()

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

def validar_usuario(request: Request):
    username = request.session.get("username")
    if username is None:
        return "Anonimo"
    else:
        return username