from fastapi import APIRouter, Request, Form, Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
#from passlib.context import CryptContext

# Importamos desde la carpeta padre (..)
from ..database import get_session
from ..models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
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


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# --- RUTA POST: Procesar el Login ---
@router.post("/login", response_class=HTMLResponse)
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
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()  # Romper la pulsera
    return RedirectResponse(url="/", status_code=303)
