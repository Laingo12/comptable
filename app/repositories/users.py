"""Accès données utilisateurs — aucune logique métier."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def by_username(self, username: str) -> User | None:
        return await self.s.scalar(select(User).where(User.username == username))

    async def by_id(self, user_id: int) -> User | None:
        return await self.s.scalar(select(User).where(User.id == user_id))

    async def list_all(self) -> list[User]:
        return list(
            (await self.s.scalars(select(User).order_by(User.username))).all()
        )

    async def create(self, **fields) -> User:
        u = User(**fields)
        self.s.add(u)
        await self.s.flush()
        return u

    async def store_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at,
        user_agent: str | None,
        ip: str | None,
        family_id: str | None = None,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip=ip,
            family_id=family_id or str(uuid4()),
        )
        self.s.add(rt)
        await self.s.flush()
        return rt

    async def find_refresh_token(self, token_hash: str) -> RefreshToken | None:
        return await self.s.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

    async def revoke_refresh_token(self, rt: RefreshToken) -> None:
        rt.revoked_at = datetime.now(timezone.utc)
        await self.s.flush()

    async def revoke_family(self, family_id: str) -> int:
        now = datetime.now(timezone.utc)
        res = await self.s.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id,
                   RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        return res.rowcount or 0

    async def revoke_all_refresh_tokens(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        res = await self.s.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id,
                   RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        return res.rowcount or 0