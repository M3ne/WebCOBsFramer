from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_form(
    request: Request,
    field1: str = Form(...),
    field2: str = Form(...)
):
    # Qui aggiungi CRC, COBS, framing ecc.
    result = f"Ricevuto: {field1}, {field2}"
    return templates.TemplateResponse("form.html", {"request": request, "result": result})