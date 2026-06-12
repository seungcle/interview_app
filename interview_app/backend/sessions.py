from __future__ import annotations

from copy import deepcopy
from typing import Literal, TypedDict
from uuid import uuid4

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


sessions: dict[str, list[Message]] = {}
session_roles: dict[str, str] = {}


def create_session(role: str = "general") -> str:
    session_id = str(uuid4())
    sessions[session_id] = []
    session_roles[session_id] = role
    return session_id


def add_message(session_id: str, role: Role, content: str) -> None:
    if session_id not in sessions:
        raise KeyError(f"unknown session_id: {session_id}")
    sessions[session_id].append({"role": role, "content": content})


def get_history(session_id: str) -> list[Message]:
    if session_id not in sessions:
        raise KeyError(f"unknown session_id: {session_id}")
    return deepcopy(sessions[session_id])


def get_session_role(session_id: str) -> str:
    return session_roles.get(session_id, "general")


def set_session_role(session_id: str, role: str) -> None:
    if session_id not in sessions:
        raise KeyError(f"unknown session_id: {session_id}")
    session_roles[session_id] = role


def clear_session(session_id: str) -> None:
    if session_id not in sessions:
        raise KeyError(f"unknown session_id: {session_id}")
    sessions[session_id] = []
