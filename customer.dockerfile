FROM python:3

RUN mkdir -p /opt/src/shop
WORKDIR /opt/src/shop

COPY ShopManagement/customer/application.py ./application.py
COPY ShopManagement/configuration.py ./configuration.py
COPY ShopManagement/models.py ./models.py
COPY ShopManagement/requirements.txt ./requirements.txt
COPY ShopManagement/roleChechDecorator.py ./roleChechDecorator.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/shop"

ENTRYPOINT ["python", "./application.py"]