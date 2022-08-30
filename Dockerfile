FROM apache/airflow:2.3.3
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN rm requirements.txt
COPY ./dags dags
COPY ./plugins plugins
COPY ./airflow.cfg airflow.cfg

USER 0
RUN apt-get update
RUN apt-get install -y chromium
USER 50000