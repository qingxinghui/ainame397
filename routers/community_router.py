from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from schemas.community_schemas import PollCreateIn, PollListOut, PollOut, PollVoteIn
from services.community_service import create_poll, get_poll, list_polls, vote_poll


router = APIRouter(prefix="/community", tags=["灵感投票所"])
auth_handler = AuthHandler()


@router.post("/polls", response_model=PollOut)
async def create_naming_poll(
    data: PollCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await create_poll(session, int(user_id), data)


@router.get("/polls", response_model=PollListOut)
async def get_poll_list(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
):
    return await list_polls(session, offset, limit)


@router.get("/polls/{poll_id}", response_model=PollOut)
async def get_naming_poll(poll_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await get_poll(session, poll_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/polls/{poll_id}/vote", response_model=PollOut)
async def vote_naming_poll(
    poll_id: int,
    data: PollVoteIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await vote_poll(session, poll_id, data.option_id, int(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
