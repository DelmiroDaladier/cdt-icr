FROM python:3.10.6

ENV DockerHOME=/home/app/webapp
ENV PYTHONUNBUFFERED=1

RUN mkdir -p $DockerHOME

WORKDIR $DockerHOME

RUN pip install --upgrade pip  

COPY . $DockerHOME 

RUN ls -a
RUN pwd 


RUN pip install -r requirements.txt  

RUN python -m spacy download en_core_web_sm

RUN git clone https://github.com/DelmiroDaladier/icr.git icr_frontend

EXPOSE 8000  

RUN chmod +x /home/app/webapp/start.sh
ENTRYPOINT ["./start.sh"]

#CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "icr.wsgi:application"]