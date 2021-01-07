FROM python:3.6
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY mysql_config.py ./
COPY app.py ./

# Set the CMD to your handler
CMD [ "python3","-u", "app.py" ]
