from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pwdlib import PasswordHash
from . import Base

password_hash = PasswordHash.recommended()

# 用这个类的时候 User(id=1，email=23424@qq.com，username=zs，passwor=lisi)
# user.password = 11111
# user.password
class User(Base):
    __tablename__ = "user"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100),unique=True)
    username:Mapped[str] = mapped_column(String(100))
    # 数据库中存储的是加密后的密码，不是明文  123456
    _password:Mapped[str] = mapped_column(String(200))

    # 1.校验数据：密码是否正确  触发时机：当你通过类实例化创建一个新对象时
    #  *args 能够接收任意多个不带名字的参数  列表
    #  **kwargs 能接受任意多个带名字的参数  字典
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = kwargs.pop("password", None)
        if password:
            # 增加了一个变量 password  设置password，会自动调用@password.setter
            self.password = password

    # 凡是获取password的时候，就调用这个函数
    @property
    def password(self):
        return self._password

    # 设置password  默认调用  凡是你给passwor赋值，都会调用这一个函数
    @password.setter
    def password(self,password):
        self._password=password_hash.hash(password)

    # 校验密码  你登录淘宝，随便输入一个秘密，它会报告，密码错误。
    def check_password(self,password):
        return password_hash.verify(password,self._password)

class EmailCode(Base):
    __tablename__ = "email_code"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100))
    code:Mapped[str] = mapped_column(String(100))
    # 发送的验证码有时效
    created_time:Mapped[datetime] = mapped_column(DateTime,default=datetime.now())


