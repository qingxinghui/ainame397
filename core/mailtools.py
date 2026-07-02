from fastapi_mail import FastMail, ConnectionConfig
from pydantic import SecretStr,EmailStr
import settings

def create_mail_instance():
    config=ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_USE_SSL,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    return FastMail(config)
