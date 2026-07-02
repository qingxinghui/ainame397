import random
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from fastapi_mail import MessageSchema, MessageType
from pydantic import EmailStr
from fastapi_mail import FastMail

router = APIRouter(prefix="/auth", tags=["auth"])
# 发送验证码给用户
from dependencies import get_email,get_session
from repository.user_repo import EmailCodeRepository
from sqlalchemy.ext.asyncio.session import AsyncSession

# EmailStr 是pydantic专门用来校验数据格式是否是邮箱的类
from core.redisconfig import get_redis_client

from redis.asyncio.client import Redis
# 发送验证码的本质是做两件事：1.发送一个验证码给用户
#                         2.保存这个验证码到数据库
@router.get("/code")
async def get_email_code(email: Annotated[EmailStr,Query(...)],
                         fastmail:FastMail=Depends(get_email),
                         session:AsyncSession=Depends(get_session),
                         redis:Redis=Depends(get_redis_client)):
    # 1.生成验证码  digits = '0123456789'
    #  4位数的验证码  0123456789012345678901234567890123456789
    source = string.digits*4
    # sample的意思是从source这个字符串随机取4位数
    # sample的返回值是一个list，我们需要的验证码是一个字符串
    # code 就是我们生成的验证码
    code = "".join(random.sample(source,4))
    # 2.创建一个邮件  系统把邮件发给谁
    message = MessageSchema(
        subject="【ai起名字app】注册验证码",
        recipients=[email],
        body=f"您的验证码是：{code},五分钟内有效，请及时注册账号",
        subtype=MessageType.plain
    )
    # 3.发送邮件
    await fastmail.send_message(message)
    # 4.把发送的邮件信息保存起来
    # email_repository = EmailCodeRepository(session=session)
    # await email_repository.create_email_code(email,code)
    # redis存储的key和value，key是我们设计的，所以，取值的时候，也要用同样的规则
    await  redis.set(email,code,ex=300)

    return {"message":"验证码发送成功"}

from schemas.user_schemas import RegisterIn, UserCreateSchema, LoginIn
from repository.user_repo import UserRepository
# 功能：用户注册。用户注册的本质是向用户表插入一条数据
#  用户在页面上填写自己的信息：用户名，密码，性别，邮箱等等。
#  后台要接收用户的信息。可以设计对象来接收，把接收对象转成数据库对象，存入数据库
@router.post("/register")
async def register(userinfo:RegisterIn,session:AsyncSession=Depends(get_session),
                   redis:Redis=Depends(get_redis_client)):
    # 向用户表插入数据
    userRepository = UserRepository(session=session)
    # 用户传过来的信息中需要一些校验
    # 1.邮箱是否已经别别人注册了  该邮箱已注册，请直接登录
    email_exist = await userRepository.email_is_exist(userinfo.email)
    if email_exist:
        raise HTTPException(status_code=400,detail="该邮箱已经注册，请直接登录")
    # 2.看验证码是否正确，如果不对，不允许注册
    # emailCodeRepository = EmailCodeRepository(session=session)
    # email_code_bool = await emailCodeRepository.check_email_code(userinfo.email,userinfo.code)
    # key是email
    email_code = await redis.get(userinfo.email)
    if (not email_code) or (userinfo.code != email_code):
        raise HTTPException(400,detail="验证码错误或者已经过期")


    # 3.允许注册  插入一条数据到数据库
    userCreatSchema = UserCreateSchema(email=userinfo.email, username=userinfo.username, password=userinfo.password)
    await userRepository.create_user(userCreatSchema)

    # 注册成功，删除redis中的数据  防止重新这侧
    # await redis.delete(userinfo.email)
    return {"message":"恭喜您注册成功"}

from  models.user import User
from core.auth import AuthHandler
from schemas.user_schemas import LoginOut
authHandler = AuthHandler()
@router.post("/login", response_model=LoginOut)
async def login(userinfo:LoginIn,session:AsyncSession=Depends(get_session)):
    # 获取你的信息，邮箱，根据有想才能知道你是不是我们的会员
    # 1. 因为你想登录，我们得确定你是已经注册的用户，未注册的不让登陆
    userRepository = UserRepository(session=session)
    # 数据库查询
    user:User|None = await  userRepository.get_user_by_email(userinfo.email)
    if not user:
        raise HTTPException(status_code=400,detail="该用户不存在！")
    # 2.看密码对不对，密码错误不让登陆
    if not user.check_password(userinfo.password):
        raise HTTPException(status_code=400, detail="密码输入错误，请核对后输入！")
    # 3.密码正确，允许登录。登录的方法是，给用户返回一个令牌。用户拿着这个令牌，下次来证明是登录过了。
    tokens = authHandler.encode_login_token(user.id)
    return {
        "user": user,
        "token": tokens['access_token']
    }