from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

# Imports relativos
from ..database import get_session
from ..models import Question, Answer

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/question", response_class=HTMLResponse)
async def question(request: Request, session: Session = Depends(get_session)):
    query = select(Question).order_by(Question.uploaded_at.desc())
    questions = session.exec(query).all()
    return templates.TemplateResponse("question.html", {"request": request,
                                                        "questions": questions})
@router.post("/question")
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
    new_question= Question(content=content, uploaded_by=final_author, uploaded_at=datetime.now())
    session.add(new_question)
    session.commit()
    session.refresh(new_question)
    return RedirectResponse(url="/question",status_code=303)

@router.get("/question/{question_id}", response_class=HTMLResponse)
async def question_detail(
        request: Request,
        question_id: int,  # FastAPI extrae este número de la URL
        session: Session = Depends(get_session)
):
    # 1. Buscamos la pregunta por su ID y sus RTAS
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    query = select(Answer).where(Answer.question_id == question_id).order_by(Answer.uploaded_at.desc())
    answers = session.exec(query).all()

    opciones = ["Bauti", "Hipo", "Rata", "Dama","Choco", "Enzo","Lauri", "Passa", "Juanito", "Lalo", "Franza", "Giampe", "Meteo", "Pato"]
    conteos = {nombre: 0 for nombre in opciones}
    for answer in answers:
        # Como guardamos "Lauri, Hipo", hay que separar el string
        seleccionados = answer.content.split(", ")

        for persona in seleccionados:
            if persona in conteos:
                conteos[persona] += 1
    # 2. Si no existe (alguien puso un ID falso en la URL), damos error 404
    lista_votos = [conteos[nombre] for nombre in opciones]

    # 3. Renderizamos la nueva plantilla pasando el objeto 'question'
    return templates.TemplateResponse("questioninfo.html", {
        "request": request,
        "question": question,
        "answers": answers,
        "opciones": opciones,
        "votos": lista_votos
    })

@router.post("/question/{question_id}/answer")
async def question_answer(
    request: Request,
    question_id: int, #
    content: List[str] = Form(...),
    session: Session = Depends(get_session)
):
    username = request.session.get("username")
    # Si es None (no está logueado), lo mandamos al login inmediatamente
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    content = ", ".join(content)
    new_answer = Answer(content=content,
                        question_id=question_id,
                        uploaded_at=datetime.now(),
                        uploaded_by=username)
    session.add(new_answer)
    session.commit()
    session.refresh(new_answer)
    return RedirectResponse(url=f"/question/{question_id}",status_code=303)



