from __future__ import annotations

import logging
from typing import Protocol

from fastapi import Request
from fastapi.responses import Response

PROFILE_COOKIE_NAME = "pcoll_profile_id"
PROFILE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


class ProfileRepository(Protocol):
    def get_or_create(self, profile_id: str | None) -> tuple[dict, bool]:
        ...


def ensure_profile(
    request: Request,
    *,
    repository: ProfileRepository,
    logger: logging.Logger | None = None,
    log_context: str = "",
) -> tuple[dict, bool]:
    profile, created = repository.get_or_create(request.cookies.get(PROFILE_COOKIE_NAME))
    if created and logger is not None:
        suffix = f" {log_context}" if log_context else ""
        logger.info(
            "Створено новий профіль користувача%s: profile_id=%s",
            suffix,
            profile.get("id"),
        )
    return profile, created


def set_profile_cookie(
    response: Response,
    *,
    profile_id: str,
    current_cookie: str | None,
) -> None:
    if str(current_cookie or "").strip() == str(profile_id or "").strip():
        return

    response.set_cookie(
        PROFILE_COOKIE_NAME,
        profile_id,
        max_age=PROFILE_COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
