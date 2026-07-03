from datetime import datetime

from pydantic import BaseModel, Field


class PollOptionIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    moral: str = Field("", max_length=1000)


class PollCreateIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    description: str = Field("", max_length=1000)
    options: list[PollOptionIn] = Field(..., min_length=2, max_length=10)


class PollVoteIn(BaseModel):
    option_id: int


class PollOptionOut(BaseModel):
    id: int
    name: str
    moral: str
    vote_count: int

    model_config = {"from_attributes": True}


class PollOut(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    status: str
    created_at: datetime
    total_votes: int
    options: list[PollOptionOut]


class PollListOut(BaseModel):
    polls: list[PollOut]
    total: int
