from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from cobs import cobs
import crcmod



# CRC16-CCITT function (0x1021 is the poly, 0xFFFF initial value)
crc16_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0xFFFF, xorOut=0x0000)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})



def splitTextCommand(cmd:str):
    cmd = cmd.strip()
    cmd_splitted= cmd.split(' ',6)
    
    nodeID = 0
    command = ''
    index = 0
    subIndex = 0
    dataType = ''
    data = ''
    err = 1
    try:
        if len(cmd_splitted) == 6:
            nodeID = int(cmd_splitted[0])
            command = cmd_splitted[1]
            index = int(cmd_splitted[2], 16)
            
            if cmd_splitted[3].count('0x') > 0:
                subIndex = int(cmd_splitted[3], base=16)
            else:
                subIndex = int(cmd_splitted[3])
                
            dataType = cmd_splitted[4]
            data = cmd_splitted[5]
            err = 0

    except ValueError:
        err = 2

    return nodeID,command,index,subIndex,dataType,data,err

def convertCommandStrToInt(cmdStr:str):
    cmdStr = cmdStr.lower()
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

def convertDataStrToBytes(dataStr:str, dataTypeStr:str):
    arr =  bytearray(b'')
    #TODO: change this in case of other data type are handled
    try:
        if dataStr.count('0x') > 0:
            dataInt = int(dataStr, base=16)
        else:
            dataInt = int(dataStr)
            
        if dataTypeStr == 'boolean':
            if dataInt != 0 or dataInt != 1:
                return arr
            else:
                arr += dataInt.to_bytes(1, byteorder='little')
        elif dataTypeStr == 'i8':
            value = dataInt.to_bytes(1, byteorder='little',  signed=True )
            arr += value
        elif dataTypeStr == 'u8':
            if dataInt < 0:
                return arr
            else:
                value = dataInt.to_bytes(1, byteorder='little')
                arr += value
        elif dataTypeStr == 'i16':
            value = dataInt.to_bytes(2, byteorder='little',  signed=True )
            arr += value
        elif dataTypeStr == 'u16':
            if dataInt < 0:
                return arr
            else:
                value = dataInt.to_bytes(2, byteorder='little')
                arr += value
        elif dataTypeStr == 'i32':
            value = dataInt.to_bytes(4, byteorder='little',  signed=True )
            arr += value
        elif dataTypeStr == 'u32':
            if dataInt < 0:
                return arr
            else:
                value = dataInt.to_bytes(4, byteorder='little')
                arr += value
        elif dataTypeStr == 'i64':
            value = dataInt.to_bytes(8, byteorder='little',  signed=True )
            arr += value
        elif dataTypeStr == 'u64': # u64
            if dataInt < 0:
                return arr
            else:
                value = dataInt.to_bytes(8, byteorder='little')
                arr += value
    except Exception:
        arr = []
    
        
    return arr
    

@app.post("/process", response_class=HTMLResponse)
async def process_form(
    request: Request,
    inputString: str = Form(...),
    frameType: str = Form(...),
    frameDelimiter: str = Form(...)
):
    # Qui aggiungi CRC, COBS, framing ecc.
    # Convert inputs to bytes (assuming 16-bit unsigned integers)
    
    nodeID,commandStr,index,subIndex,dataTypeStr,dataStr, err = splitTextCommand(inputString)
    
    if err == 1:
        result = "Command not recognized: wrong number of parameters"
        return templates.TemplateResponse("form.html", {"request": request, "result": result})
    elif err == 2:
        result = "Command not recognized: impossible to convert to int one or more parameters"
        return templates.TemplateResponse("form.html", {"request": request, "result": result})
    
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
    
    payloadArr = convertDataStrToBytes(dataStr,dataTypeStr)
    
    if payloadArr == []:
        result = "Command not recognized: last element wrong (number to be complient with the type)"
        return templates.TemplateResponse("form.html", {"request": request, "result": result})

    data_array = bytearray(b'')
    
    if frameType != 'none':
        frameTypeint = int(frameType)
        data_array += frameTypeint.to_bytes(1, byteorder='little')
    
    data_array += nodeID.to_bytes(1, byteorder='little')
    data_array += commandInt.to_bytes(1, byteorder='little')
    data_array += index.to_bytes(2, byteorder='little')
    data_array += subIndex.to_bytes(1, byteorder='little')
    data_array += dataTypeInt.to_bytes(1, byteorder='little')
    data_array += payloadArr

    # Calculate CRC16
    crc = crc16_func(data_array)
    crc_bytes = crc.to_bytes(2, byteorder='little')

    # Final frame = data + CRC
    frame = data_array + crc_bytes
    
    
    # Encode using COBS and add frame delimiter
    if len(frameDelimiter) > 0:
        frameDelimiterInt = int(frameDelimiter, base=16)
        encoded  = frameDelimiterInt.to_bytes(1, byteorder='little') + cobs.encode(frame) + frameDelimiterInt.to_bytes(1, byteorder='little')
    else:
        encoded  = cobs.encode(frame)

    result_list = [f"0x{b:02X}" for b in encoded]
    result = f"[{', '.join(result_list)}]"
    
    print(result)
    return templates.TemplateResponse("form.html", {"request": request, "result": result})