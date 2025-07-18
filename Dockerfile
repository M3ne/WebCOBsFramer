FROM python:3.12.7


WORKDIR /code

COPY . /code/app

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt

CMD ["fastapi", "run", "app/main.py", "--port", "80"]