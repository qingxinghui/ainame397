from typing import Annotated
from pydantic import BaseModel, EmailStr, Field, model_validator, ValidationError

# 接收用户传过来的数据的一个对象
RawPasswordStr = Annotated[str,Field(...,min_length=4,max_length=50)]
RawUserNameStr =Annotated[str,Field(...,min_length=4,max_length=50)]
class RegisterIn(BaseModel):
    email:EmailStr
    username:RawUserNameStr
    password:RawPasswordStr
    confirm_password:RawPasswordStr
    # 验证用户的有效性
    code:Annotated[str,Field(...,min_length=4,max_length=4)]

    # 完成确认密码的校验
    @model_validator(mode="after")
    def password_is_valid(self,password:str) -> bool:
        password = self.password
        confirm_password = self.confirm_password
        if password != confirm_password:
            raise ValidationError("Passwords don't match")
        return self

# 存入数据库的是少数字段
class UserCreateSchema(BaseModel):
    email:EmailStr
    username:RawUserNameStr
    password:RawPasswordStr

# 开发对象，接收用户登录信息
class LoginIn(BaseModel):
    email:EmailStr
    password:RawPasswordStr

class UserSchema(BaseModel):
    id:Annotated[int,Field(...)]
    username: RawUserNameStr
    email: EmailStr

from models.user import User
class LoginOut(BaseModel):
    user:UserSchema
    token: str