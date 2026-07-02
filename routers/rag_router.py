# import os
# import shutil
# from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
# from core.auth import AuthHandler
# # from core.rag_service import process_and_store_file
#
# auth_handler = AuthHandler()
# router = APIRouter(prefix="/knowledge", tags=["企业知识库"])
#
# # 启动项目所在的根文件的路径，在我们项目中是ai397下main创建一个文件夹uploads
# UPLOAD_DIR = "./uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)
#
# from core.rag_service import process_and_stor_file
# @router.post("/upload")
# async def upload_file(background_tasks: BackgroundTasks,file: UploadFile = File(...), user_id: int = Depends(auth_handler.auth_access_dependency)):
#     """
#     用户上传专属参考文件（TXT/PDF）
#     """
#     # 第一步：完成文件在服务器的保存
#     file_path =os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
#
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#
#     # 第二步：把已经上传的文件，插入到知识库的数据库中
#     background_tasks.add_task(process_and_stor_file,file_path,user_id)
#
#     return {
#         "result": "success",
#         "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
#     }

import os
import shutil
import json
import aio_pika
from fastapi import APIRouter, UploadFile, File, Depends
from core.auth import AuthHandler
import settings

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["知识库"])

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# RabbitMQ 连接配置 协议://用户名:密码@主机地址:端口号
RABBITMQ_URL = settings.RABBITMQ_URL
QUEUE_NAME = settings.RAG_QUEUE_NAME


async def send_to_queue(message_dict: dict):
    """异步将任务发送到 RabbitMQ 队列"""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # declare_queue，如果没有，创建。声明队列：durable=True 开启持久化，服务器重启任务不丢
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        # 将任务字典转为 JSON 字节流发送
        message_body = json.dumps(message_dict).encode("utf-8")
        # 调用默认交换机，把封装好的消息发布出去
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            # 路由键只要和队列名字一模一样
            routing_key=queue.name,
        )


from core.rag_service import process_and_stor_file


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: int = Depends(auth_handler.auth_access_dependency)):
    """
    用户上传专属参考文件（TXT/PDF）
    """
    # 第一步：完成文件在服务器的保存
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    # 注意这里转换成绝对路径
    absolute_path = os.path.abspath(file_path)
    with open(absolute_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 第二步：把已经上传的文件，插入到知识库的数据库中
    # background_tasks.add_task(process_and_stor_file, file_path, user_id)
    # 2. 构造任务包裹并投递
    task_message = {
        "user_id": user_id,
        "file_path": absolute_path
    }
    await send_to_queue(task_message)

    return {
        "result": "success",
        "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
    }

