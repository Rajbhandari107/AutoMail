from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="AutoMail API",
    description="Email outreach automation backend",
    version="1.0.0"
)


app.include_router(router)