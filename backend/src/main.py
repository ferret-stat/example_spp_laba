from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.create_user import router as create_user
from src.routers.authorization import router as auth_router
from src.routers.files_router import router as files_router
from src.routers.description import router as desc_router
from src.routers.comments import router as comments_router
from src.routers.file_like import router as like_router
from src.routers.admin import router as admin_router


app = FastAPI()

origins = [
    "http://localhost:5173",  
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(create_user, prefix='/auth')
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(desc_router)
app.include_router(comments_router)
app.include_router(like_router)
app.include_router(admin_router)
