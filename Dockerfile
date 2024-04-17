FROM python:3.10
WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
EXPOSE 80
CMD ["gunicorn", "-w", "4","-b", "'[::]:80'", "app:app"]