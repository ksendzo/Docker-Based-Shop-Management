from datetime import timedelta
import os

databaseUrl = os.environ["DATABASE_URL"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/authentication"
    # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@localhost:3309/user"
    REDIS_HOST = "localhost"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRESS = timedelta(seconds=int(60*60))
    JWT_REFRESH_TOKEN_EXPIRESS = timedelta(seconds=int(30*24*60*60))


