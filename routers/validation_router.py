from fastapi import APIRouter, Depends

from core.auth import AuthHandler
from core.validation_service import validate_assets
from schemas.validation_schemas import AssetValidationIn, AssetValidationOut


router = APIRouter(prefix="/validation", tags=["数字资产校验"])
auth_handler = AuthHandler()


@router.post("/check", response_model=AssetValidationOut)
async def check_name_assets(
    data: AssetValidationIn,
    _user_id: int = Depends(auth_handler.auth_access_dependency),
):
    return await validate_assets(data)
