from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from .config import Settings, get_settings
from .domain import UserContext


@dataclass(slots=True)
class OIDCVerifier:
    issuer: str
    audience: str
    jwks_url: str

    def verify(self, token: str) -> dict[str, object]:
        client = PyJWKClient(self.jwks_url, cache_keys=True, lifespan=300)
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=self.audience,
            issuer=self.issuer,
            options={"require": ["exp", "iat", "sub"]},
        )


def _claim_as_string(claims: dict[str, object], key: str, default: str) -> str:
    value = claims.get(key)
    return value if isinstance(value, str) and value else default


async def get_user_context(
    authorization: str | None = Header(default=None),
    x_nexus_user_role: str = Header(default="employee"),
    x_nexus_user_department: str = Header(default="Software Engineering"),
    x_nexus_user_country: str = Header(default="GLOBAL"),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    if settings.auth_mode == "dev_headers":
        return UserContext(
            role=x_nexus_user_role[:64],
            department=x_nexus_user_department[:128],
            country=x_nexus_user_country[:16].upper(),
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required"
        )

    token = authorization.removeprefix("Bearer ").strip()
    verifier = OIDCVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        jwks_url=settings.oidc_jwks_url,
    )
    try:
        claims = await asyncio.to_thread(verifier.verify, token)
    except (jwt.PyJWTError, httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    return UserContext(
        subject=_claim_as_string(claims, "sub", "unknown"),
        role=_claim_as_string(claims, "role", "employee"),
        department=_claim_as_string(claims, "department", "unknown"),
        country=_claim_as_string(claims, "country", "GLOBAL").upper(),
    )
