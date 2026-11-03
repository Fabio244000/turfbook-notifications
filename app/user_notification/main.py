from fastapi import FastAPI
from mangum import Mangum

from app.user_notification.infrastructure.api.v1_router import router as v1_router
from config.settings import settings

app = FastAPI(title='TurfBook Notifications Service')

app.include_router(v1_router, prefix=settings.api_prefix)

handler = Mangum(app, lifespan='off')
