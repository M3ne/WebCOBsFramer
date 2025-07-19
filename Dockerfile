FROM python:3.12.7

EXPOSE 80

WORKDIR /code

COPY . /code/app

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt

WORKDIR /code/app

CMD ["fastapi", "run", "main.py", "--port", "80"]