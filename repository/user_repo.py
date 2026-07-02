from sqlalchemy.ext.asyncio.session import AsyncSession
from models.user import User, EmailCode
from sqlalchemy import select, update, delete, exists
from datetime import datetime, timedelta

from schemas.user_schemas import UserCreateSchema


# 与email表交互的一个对象
class EmailCodeRepository():

    def __init__(self,session: AsyncSession):
       self.session = session

    # 把一条emailcode数据插入到数据库
    async def create_email_code(self,email:str,code:str):
        async with self.session.begin():
           # 准备与email_code表对应的一个对象
           email_code = EmailCode(email=email,code=code)
           self.session.add(email_code)

           return email_code

    # 这是对验证码的校验函数
    async def check_email_code(self,email:str,code:str):
        async with self.session.begin():
            #  select * from emailcode where email="" and code=""
           email_code  = await  self.session.scalar(select(EmailCode)
                                                    .filter(EmailCode.email==email,EmailCode.code==code))
           #  数据库如果没有emil_code这个类，说明没有给你发送验证码
           if not email_code:
               return False
           # 如果过期了，超过5分钟，验证码失效
           if(datetime.now() - email_code.created_time) >= timedelta(minutes=5):
               return False
           return True
# 与user表交互的对象
class UserRepository():
    def __init__(self,session: AsyncSession):
        self.session = session

    # 我判断用户传过来的邮箱是否已经被他人注册过。
    async def get_user_by_email(self,email:str):
        async with self.session.begin():
            result = await self.session.execute(select(User).where(User.email==email))
            return result.scalar_one_or_none()

    # 插入一条数据
    async def create_user(self,user:UserCreateSchema):
        async with self.session.begin():
            # user.model_dump() 把对象属性数据变成字典
            # **是解包  User(email=“xx@qq.com”,username="")
            user = User(**user.model_dump())
            self.session.add(user)
            return user
    # 我判断用户传过来的邮箱是否已经被他人注册过。
    async def email_is_exist(self,email:str):
        async with self.session.begin():
            stmt = select(exists().where(User.email == email))
            return await self.session.scalar(stmt)
