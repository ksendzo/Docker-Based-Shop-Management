from datetime import timedelta
import os

databaseUrl = os.environ["DATABASE_URL"]

class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/shop"
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost:3310/shop"
    REDIS_HOST = "redis"
    REDIS_PRODUCT_LIST = "products"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    # JWT_ACCESS_TOKEN_EXPIRESS = timedelta(hours=1)
    # JWT_REFRESH_TOKEN_EXPIRESS = timedelta(days=30)
    # REDIS_URL = "redis://localhost:6380"


