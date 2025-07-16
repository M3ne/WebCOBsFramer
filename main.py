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



def splitTextCommand(cmd:str):
    
    cmd_splitted= cmd.split(' ',6)
    nodeID = int(cmd_splitted[0])
    command = cmd_splitted[1]
    index = int(cmd_splitted[2], 16)
    subIndex = int(cmd_splitted[3])
    dataType = cmd_splitted[4]
    data = cmd_splitted[5]

    return nodeID,command,index,subIndex,dataType,data

def convertCommandStrToInt(cmdStr:str):
    cmdInt = -1
    if cmdStr == 'w':
        cmdInt = 1
    elif cmdStr == 'r':
        cmdInt = 2
        
    return cmdInt

def convertDataTypeStrToInt(dataTypeStr:str):
    dataTypeInt = -1
    
    dataTypeStr = dataTypeStr.lower()
    
    if dataTypeStr == "boolean":
        dataTypeInt = 0
    elif dataTypeStr == "i8":
        dataTypeInt = 1
    elif dataTypeStr == "i16":
        dataTypeInt = 2
    elif dataTypeStr == "i32":
        dataTypeInt = 3
    elif dataTypeStr == "i64":
        dataTypeInt = 4
    elif dataTypeStr == "u8":
        dataTypeInt = 5
    elif dataTypeStr == "u16":
        dataTypeInt = 6
    elif dataTypeStr == "u32":
        dataTypeInt = 7
    elif dataTypeStr == "u64":
        dataTypeInt = 8
        
    
    return dataTypeInt

def convertDataStrToBytes(dataStr:str, dataTypeInt:int):
    arr = []
    #TODO: change this in case of other data type are handled
    dataInt = int(dataStr)
    if dataTypeInt == 0: # boolean
        if value != 0 or value != 1:
            return arr
        else:
            arr.append(value.to_bytes(1, byteorder='big'))
    elif dataTypeInt == 1 or dataTypeInt == 5: # i8 or u8
        value = dataInt.to_bytes(1, byteorder='big')
        arr.append(value)
    elif dataTypeInt == 2 or dataTypeInt == 6: # i16 or u16
        value = dataInt.to_bytes(2, byteorder='big')
        arr.append(value)
    elif dataTypeInt == 3 or dataTypeInt == 7: # i32 or u32
        value = dataInt.to_bytes(4, byteorder='big')
        arr.append(value)
    elif dataTypeInt == 4 or dataTypeInt == 8: # i64 or u64
        value = dataInt.to_bytes(8, byteorder='big')
        arr.append(value)
    
        
    
    return arr
    

@app.post("/process", response_class=HTMLResponse)
async def process_form(
    request: Request,
    commandTxt: str = Form(...)
):
    # Qui aggiungi CRC, COBS, framing ecc.
    # Convert inputs to bytes (assuming 16-bit unsigned integers)
    
    
    nodeID,commandStr,index,subIndex,dataTypeStr,dataStr = splitTextCommand(commandTxt)
    
    commandInt = convertCommandStrToInt(commandStr)
    dataTypeInt = convertDataTypeStrToInt(dataTypeStr)
    
    if commandInt == -1 or dataTypeInt == -1 :
        result = ""
        if commandInt == -1:
            result = "Command not recognized: Second element wrong (use w or r)"
        else:
            result = "Command not recognized: Fifth element wrong (use <boolean, i8, u8, i16, u16, i32, u32, i64, u64>)"
        
        return templates.TemplateResponse("form.html", {"request": request, "result": result})
    
    payloadArr = []
    
    payloadArr = convertCommandStrToInt(dataStr,dataTypeInt)
    
    if payloadArr == []:
        result = "Command not recognized: last element wrong (number to be complient with the type)"
        return templates.TemplateResponse("form.html", {"request": request, "result": result})

    

    
    data_array = []
    data_array.append(nodeID.to_bytes(1, byteorder='big'))
    data_array.append(commandInt.to_bytes(1, byteorder='big'))
    data_array.append(index.to_bytes(2, byteorder='big'))
    data_array.append(subIndex.to_bytes(1, byteorder='big'))
    data_array.append(dataTypeInt.to_bytes(1, byteorder='big'))
    data_array.append(payloadArr)

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