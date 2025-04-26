from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from cobs import cobs
import crcmod



# CRC16-CCITT function (0x1021 is the poly, 0xFFFF initial value)
crc16_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0xFFFF, xorOut=0x0000)


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_form(
    request: Request,
    field1: int = Form(...),
    field2: int = Form(...)
):
    # Qui aggiungi CRC, COBS, framing ecc.
    # Convert inputs to bytes (assuming 16-bit unsigned integers)
    bytes_val1 = field1.to_bytes(1, byteorder='big')
    bytes_val2 = field2.to_bytes(1, byteorder='big')

    # Combine into a byte array
    data_array = bytes_val1 + bytes_val2

    # Calculate CRC16
    crc = crc16_func(data_array)
    crc_bytes = crc.to_bytes(2, byteorder='big')

    # Final frame = data + CRC
    frame = data_array + crc_bytes

    # Encode using COBS
    encoded = cobs.encode(frame)

    result_list = [f"0x{b:02X}" for b in encoded]
    result = f"Ricevuto: [{', '.join(result_list)}]"
    return templates.TemplateResponse("form.html", {"request": request, "result": result})