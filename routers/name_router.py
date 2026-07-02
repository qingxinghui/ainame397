from fastapi import APIRouter,Depends
from schemas.name_schemas import NameIn,NameOutSchema
# from core.nametools import generate_names
from core.workflow import generate_naming
from core.auth import AuthHandler

auth_handler = AuthHandler()
router = APIRouter(prefix="/names", tags=["names"])

# user_id: int = Depends(auth_handler.auth_access_dependency) 用户登录校验，如果没有登录，无法访问
@router.post("/get_names", response_model=NameOutSchema)
async def get_names(name_info: NameIn,user_id: int = Depends(auth_handler.auth_access_dependency)):
    # user_id 是用户创建数据库表的时候用户，当时创用id指定表明，现在查应该用相同的名字才可以
    result = await generate_naming(name_info,user_id)
    return NameOutSchema(names=result["names"])

from schemas.name_schemas import NameSchemaWithThreadOut
from core.workflow import generate_naming_v2
@router.post("/generate", response_model=NameSchemaWithThreadOut)
async def get_names(name_info: NameIn,user_id: int = Depends(auth_handler.auth_access_dependency)):
    # user_id 是用户创建数据库表的时候用户，当时创用id指定表明，现在查应该用相同的名字才可以
    result = await generate_naming_v2(name_info,user_id)
    return NameSchemaWithThreadOut(thread_id=result["thread_id"],names=result["names"]["names"])

from schemas.name_schemas import FeedbackSchema
from core.workflow import feedback_names
@router.post("/feedback", response_model=NameSchemaWithThreadOut)
async def feedback(data:FeedbackSchema,user_id: int = Depends(auth_handler.auth_access_dependency)):
    result = await feedback_names(data, user_id)
    return NameSchemaWithThreadOut(thread_id=result["thread_id"], names=result["names"]["names"])

