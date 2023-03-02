FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY UserAccountManagement/migrate.py ./migrate.py
COPY UserAccountManagement/configuration.py ./configuration.py
COPY UserAccountManagement/models.py ./models.py
COPY UserAccountManagement/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]
