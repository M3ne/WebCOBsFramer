
# WebCOBsFramer

Website having as input some parameters. The backend concatenate those data, apply a CRC and create a frame using the COBs protocol and apply a packet delimiter.

  

# Try it locally

## Environment Installation
- Create a virtual environment:
  `python -m venv ./venv`
  
- Activate it:
 `.\venv\Scripts\Activate.ps1`

- Install dependencies in requirements.txt
 `pip install -r .\requirements.txt `


> - Local server could be create with fastAPI server:
>
>	- Install fastapi:
 >`pip install "fastapi[standard]" `
>
>	- Run server:
> `fastapi.exe dev .\main.py `
 
 ## Run
 If using fastapi, the local version could be load on a browser at http://127.0.0.1:8000

Result:
![WebCOBsFramer interface](/images/landingPage.png)