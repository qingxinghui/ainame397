from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.community import NamingPoll, NamingPollOption, NamingPollVote
from schemas.community_schemas import PollCreateIn, PollListOut, PollOptionOut, PollOut


def _serialize_poll(poll: NamingPoll) -> PollOut:
    options = [PollOptionOut.model_validate(option) for option in poll.options]
    return PollOut(
        id=poll.id,
        creator_id=poll.creator_id,
        title=poll.title,
        description=poll.description,
        status=poll.status,
        created_at=poll.created_at,
        total_votes=sum(option.vote_count for option in poll.options),
        options=options,
    )


async def _get_poll(session: AsyncSession, poll_id: int) -> NamingPoll | None:
    result = await session.execute(
        select(NamingPoll).options(selectinload(NamingPoll.options)).where(NamingPoll.id == poll_id)
    )
    return result.scalar_one_or_none()


async def create_poll(session: AsyncSession, user_id: int, data: PollCreateIn) -> PollOut:
    async with session.begin():
        poll = NamingPoll(creator_id=user_id, title=data.title, description=data.description)
        poll.options = [NamingPollOption(name=item.name, moral=item.moral) for item in data.options]
        session.add(poll)
        await session.flush()
        poll_id = poll.id
    created = await _get_poll(session, poll_id)
    return _serialize_poll(created)


async def get_poll(session: AsyncSession, poll_id: int) -> PollOut:
    poll = await _get_poll(session, poll_id)
    if not poll:
        raise LookupError("投票不存在")
    return _serialize_poll(poll)


async def list_polls(session: AsyncSession, offset: int = 0, limit: int = 20) -> PollListOut:
    total = await session.scalar(select(func.count()).select_from(NamingPoll)) or 0
    result = await session.execute(
        select(NamingPoll)
        .options(selectinload(NamingPoll.options))
        .where(NamingPoll.status == "active")
        .order_by(NamingPoll.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    polls = [_serialize_poll(item) for item in result.scalars().unique().all()]
    return PollListOut(polls=polls, total=total)


async def vote_poll(session: AsyncSession, poll_id: int, option_id: int, user_id: int) -> PollOut:
    poll = await _get_poll(session, poll_id)
    if not poll or poll.status != "active":
        raise LookupError("投票不存在或已结束")
    if option_id not in {item.id for item in poll.options}:
        raise ValueError("候选项不属于该投票")

    try:
        session.add(NamingPollVote(poll_id=poll_id, option_id=option_id, user_id=user_id))
        await session.execute(
            update(NamingPollOption)
            .where(NamingPollOption.id == option_id)
            .values(vote_count=NamingPollOption.vote_count + 1)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("每位用户只能投票一次") from exc

    updated = await _get_poll(session, poll_id)
    return _serialize_poll(updated)
