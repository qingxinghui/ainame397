from fastapi import FastAPI,Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_mail import FastMail, MessageSchema, MessageType
from routers.auth_router import router as auth_router
from routers.name_router import router as name_router
from routers.rag_router import router as rag_router
from routers.validation_router import router as validation_router
from routers.community_router import router as community_router

from contextlib import asynccontextmanager
from core.workflow import init_workflow_graph, close_workflow_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时，安全地初始化带记忆的工作流
    await init_workflow_graph()
    yield
    # 服务停止时，清理数据库连接
    await close_workflow_graph()
from fastapi.middleware.cors import CORSMiddleware
import os
import settings



app = FastAPI(lifespan=lifespan)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,    # 允许携带 Cookie/凭证
    allow_methods=["*"],       # 允许的请求方法（"GET", "POST", "PUT", "DELETE" 等，"*" 表示全部允许）
    allow_headers=["*"],       # 允许的请求头（"*" 表示全部允许）
)
app.include_router(auth_router)
app.include_router(name_router)
app.include_router(rag_router)
app.include_router(validation_router)
app.include_router(community_router)
@app.get("/")
async def root():
    index_file = settings.BASE_DIR / "frontend" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

from dependencies import get_email
@app.get("/mail/test")
async def mail_test(email:str,mail:FastMail=Depends(get_email)):
        #  1.准备邮件对象
        message = MessageSchema(
            subject="ainame验证码",
            recipients=[email],
            body=f"Hello {email}",  # 验证码是生产的
            subtype=MessageType.plain)

        await  mail.send_message(message)
        return {"message": "邮件发送成功！"}


frontend_dir = settings.BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")

