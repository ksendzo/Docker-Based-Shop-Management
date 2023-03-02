FROM python:3

RUN mkdir -p /opt/src/shop
WORKDIR /opt/src/shop

COPY ShopManagement/migrate.py ./migrate.py
COPY ShopManagement/configuration.py ./configuration.py
COPY ShopManagement/models.py ./models.py
COPY ShopManagement/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/shop"

ENTRYPOINT ["python", "./migrate.py"]
