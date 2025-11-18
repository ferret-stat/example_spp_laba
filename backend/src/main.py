from fastapi import FastAPI
from src.routers.create_user import router as create_user
from src.routers.authorization import router as auth_router

app = FastAPI()

app.include_router(create_user, prefix='/auth')
app.include_router(auth_router, prefix='/auth')
