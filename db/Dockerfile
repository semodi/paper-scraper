FROM public.ecr.aws/lambda/python:3.6.2020.12.18.22

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY mysql_config.py ./
COPY app.py ./

# Set the CMD to your handler
CMD [ "app.handler" ]
