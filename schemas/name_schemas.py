from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List,Literal

class NameSchema(BaseModel):
    name:Annotated[str,Field(...,description="The name of the person")]
    reference:Annotated[str,Field(...,description="The name of the person from where")]
    moral:Annotated[str,Field(...,description="寓意")]
    domain:str = Field(...,description="为该产品设计的纯小写.com域名，列如:astar.com")
    #是否被注册 查询第三方接口，根据domain,判断
    domain_status:str = Field(default="正在查询...",description="域名的注册状态S")
#  我们给大模型一个要求，让他起名字，一次性起多个名字。所以结构如下
class NameResultSchema(BaseModel):
    names:List[NameSchema]

CategoryLiteral = Literal["人名", "企业名", "宠物名"]
# 为了多类型起名改造用户输入，接收分类参数
class NameIn(BaseModel):

    category:Annotated[CategoryLiteral,Field(...,description="命名的分类")]
    surname:Annotated[str,Field("",description="The surname of the person")]
    gender:Annotated[Literal["不限", "男", "女"],Field("",description="The gender of the person")]
    length:Annotated[str,Field("",description="The length of the person")]
    other:Annotated[str|None,Field("",description="The other person")]
    exclude:Annotated[list[str],Field([],description="The exclude person")]

    @model_validator(mode="after")
    def validate(self):
        if self.category == "人名" and not self.surname:
            raise  ValueError("给人起名字时，必须给定姓氏")
        # 因为用户调用NameIn，必定期望返回的是本对象。
        return self



class NameOutSchema(BaseModel):
    names:List[NameSchema]


class NameSchemaWithThreadOut(BaseModel):
    thread_id:str
    names: List[NameSchema]




# 为了调整需求，开发一个接收参数的类
class FeedbackSchema(BaseModel):
    thread_id:str = Field(...)
    category: Literal["人名", "企业名", "宠物名"] = Field(..., description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，如：换成带水字旁的字")


