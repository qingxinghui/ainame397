from core.mailtools import create_mail_instance




async def get_email():
    return create_mail_instance()

from models import AsyncSessionFactory


async def get_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()