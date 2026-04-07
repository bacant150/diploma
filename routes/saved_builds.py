from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from config import FPS_LIMITS, STATUS_MESSAGES, TEMPLATES_DIR
from repositories.saved_builds_repository import saved_builds_repository
from repositories.user_profiles_repository import user_profiles_repository
from schemas import BuildInputsViewSchema, BuildResultSchema
from services.build_service import budget_limits_for_purpose, normalize_build_name, result_page_context
from utils.assets import attach_part_images
from utils.validation import extract_json_object

PROFILE_COOKIE_NAME = "pcoll_profile_id"
PROFILE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

logger = logging.getLogger("pcbuilder.routes.saved_builds")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


def _ensure_profile(request: Request) -> tuple[dict, bool]:
    profile, created = user_profiles_repository.get_or_create(
        request.cookies.get(PROFILE_COOKIE_NAME)
    )
    if created:
        logger.info(
            "Створено новий профіль у saved-builds маршрутах: profile_id=%s",
            profile.get("id"),
        )
    return profile, created


def _set_profile_cookie(
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
        httponly=False,
        samesite="lax",
    )


@router.get("/saved-builds", response_class=HTMLResponse)
def saved_builds_page(request: Request) -> HTMLResponse:
    status = request.query_params.get("status", "")
    profile, _ = _ensure_profile(request)
    saved_builds = [
        saved_builds_repository.prepare_for_list(build)
        for build in reversed(saved_builds_repository.load_by_profile(profile["id"]))
    ]
    builds_by_id = {build.get("id"): build for build in saved_builds}
    prepared_profile = user_profiles_repository.prepare_for_dashboard(
        profile,
        saved_builds_by_id=builds_by_id,
    )
    logger.info(
        "Відкрито сторінку профілю та збережених збірок: profile_id=%s saved_builds=%s history=%s status=%s",
        profile.get("id"),
        len(saved_builds),
        prepared_profile.get("query_count"),
        status or "none",
    )
    response = templates.TemplateResponse(
        "saved-builds.html",
        {
            "request": request,
            "profile": prepared_profile,
            "saved_builds": saved_builds,
            "status_message": STATUS_MESSAGES.get(status, ""),
        },
    )
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.get("/saved-builds/view")
def saved_build_view_page(request: Request) -> RedirectResponse:
    build_id = str(request.query_params.get("id", "") or "").strip()
    target = f"/saved-builds/{build_id}" if build_id else "/saved-builds"
    profile, _ = _ensure_profile(request)
    logger.info(
        "Redirect на перегляд збереженої збірки: profile_id=%s build_id=%s",
        profile.get("id"),
        build_id or "missing",
    )
    response = RedirectResponse(target, status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.get("/profile/history/{query_id}", response_class=HTMLResponse, response_model=None)
def open_profile_history_entry(request: Request, query_id: str) -> Response:
    profile, _ = _ensure_profile(request)
    entry = user_profiles_repository.find_query(profile["id"], query_id)
    if not entry:
        logger.warning(
            "Спроба відкрити відсутній запис історії: profile_id=%s query_id=%s",
            profile.get("id"),
            query_id,
        )
        raise HTTPException(status_code=404, detail="Запис історії не знайдено.")

    linked_build_id = str(entry.get("saved_build_id") or "").strip()
    if linked_build_id:
        saved_build = saved_builds_repository.find_by_id(linked_build_id, profile_id=profile["id"])
        if saved_build:
            logger.info(
                "Відкрито запис історії через пов’язану збережену збірку: profile_id=%s query_id=%s build_id=%s",
                profile.get("id"),
                query_id,
                linked_build_id,
            )
            result = attach_part_images(saved_build.get("result", {}))
            response = templates.TemplateResponse(
                "result.html",
                result_page_context(
                    request,
                    saved_build.get("inputs", {}),
                    result,
                    saved_build_name=saved_build.get("name"),
                    profile_query_id=entry.get("id"),
                    profile_name=profile.get("name"),
                    is_saved_build_view=True,
                ),
            )
            _set_profile_cookie(
                response,
                profile_id=profile["id"],
                current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
            )
            return response

    snapshot = entry.get("result_snapshot")
    if not isinstance(snapshot, dict) or not snapshot:
        logger.warning(
            "Для запису історії не знайдено result snapshot: profile_id=%s query_id=%s",
            profile.get("id"),
            query_id,
        )
        raise HTTPException(
            status_code=404,
            detail="Для цього запису історії не знайдено збережений результат.",
        )

    logger.info(
        "Відкрито запис історії зі snapshot: profile_id=%s query_id=%s",
        profile.get("id"),
        query_id,
    )
    result = attach_part_images(snapshot)
    response = templates.TemplateResponse(
        "result.html",
        result_page_context(
            request,
            entry.get("inputs", {}),
            result,
            profile_query_id=entry.get("id"),
            profile_name=profile.get("name"),
            is_saved_build_view=False,
        ),
    )
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.post("/profile/history/{query_id}/delete")
def delete_profile_history_entry(request: Request, query_id: str) -> RedirectResponse:
    profile, _ = _ensure_profile(request)
    deleted_entry = user_profiles_repository.delete_query(profile["id"], query_id)
    if not deleted_entry:
        logger.warning(
            "Спроба видалити відсутній запис історії: profile_id=%s query_id=%s",
            profile.get("id"),
            query_id,
        )
        raise HTTPException(status_code=404, detail="Запис історії не знайдено.")

    linked_build_id = str(deleted_entry.get("saved_build_id") or "").strip()
    if linked_build_id:
        saved_builds_repository.clear_query_reference(linked_build_id, profile_id=profile["id"])

    logger.info(
        "Видалено запис історії: profile_id=%s query_id=%s linked_build_id=%s",
        profile.get("id"),
        query_id,
        linked_build_id or "none",
    )
    response = RedirectResponse(url="/saved-builds?status=history_deleted", status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.post("/profile/history/clear")
def clear_profile_history(request: Request) -> RedirectResponse:
    profile, _ = _ensure_profile(request)
    removed_entries = user_profiles_repository.clear_query_history(profile["id"])
    query_ids = [
        str(entry.get("id") or "").strip()
        for entry in removed_entries
        if str(entry.get("id") or "").strip()
    ]
    cleared_links = 0
    if query_ids:
        cleared_links = saved_builds_repository.clear_query_references_for_profile(
            profile["id"],
            query_ids=query_ids,
        )

    logger.info(
        "Очищено історію запитів: profile_id=%s removed_entries=%s cleared_build_links=%s",
        profile.get("id"),
        len(removed_entries),
        cleared_links,
    )
    response = RedirectResponse(url="/saved-builds?status=history_cleared", status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.post("/saved-builds/save")
async def save_build(request: Request) -> RedirectResponse:
    profile, _ = _ensure_profile(request)
    form = await request.form()

    raw_inputs = extract_json_object(form.get("inputs_json", "{}"), field_name="inputs_json")
    raw_result = extract_json_object(form.get("result_json", "{}"), field_name="result_json")

    purpose = str(raw_inputs.get("purpose", "gaming") or "gaming")
    budget_limits = budget_limits_for_purpose(purpose)
    inputs = BuildInputsViewSchema.model_validate(
        raw_inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    ).model_dump(mode="json")
    result = BuildResultSchema.model_validate(raw_result).model_dump(mode="json")
    build_name = normalize_build_name(str(form.get("build_name", "")), inputs)
    query_id = str(form.get("profile_query_id", "") or "").strip() or None
    build_id = uuid4().hex

    saved_builds_repository.save_record(
        {
            "id": build_id,
            "profile_id": profile["id"],
            "query_id": query_id,
            "name": build_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "inputs": inputs,
            "result": result,
        }
    )
    user_profiles_repository.link_saved_build(profile["id"], build_id, query_id=query_id)

    logger.info(
        "Збережено збірку: profile_id=%s build_id=%s query_id=%s name=%s purpose=%s tier=%s total=%s",
        profile.get("id"),
        build_id,
        query_id or "none",
        build_name,
        inputs.get("purpose"),
        result.get("tier"),
        result.get("total") or result.get("total_price"),
    )
    response = RedirectResponse(url="/saved-builds?status=saved", status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.get("/saved-builds/{build_id}", response_class=HTMLResponse)
def open_saved_build(request: Request, build_id: str) -> HTMLResponse:
    profile, _ = _ensure_profile(request)
    saved_build = saved_builds_repository.find_by_id(build_id, profile_id=profile["id"])
    if not saved_build:
        logger.warning(
            "Спроба відкрити відсутню збережену збірку: profile_id=%s build_id=%s",
            profile.get("id"),
            build_id,
        )
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    logger.info(
        "Відкрито збережену збірку: profile_id=%s build_id=%s",
        profile.get("id"),
        build_id,
    )
    inputs = saved_build.get("inputs", {})
    result = attach_part_images(saved_build.get("result", {}))
    response = templates.TemplateResponse(
        "result.html",
        result_page_context(
            request,
            inputs,
            result,
            saved_build_name=saved_build.get("name"),
            profile_query_id=saved_build.get("query_id"),
            profile_name=profile.get("name"),
            is_saved_build_view=True,
        ),
    )
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.post("/saved-builds/{build_id}/rename")
def rename_saved_build(
    request: Request,
    build_id: str,
    build_name: str = Form(...),
) -> RedirectResponse:
    profile, _ = _ensure_profile(request)
    existing_build = saved_builds_repository.find_by_id(build_id, profile_id=profile["id"])
    normalized_name = normalize_build_name(build_name, existing_build.get("inputs", {}) if existing_build else {})
    updated_build = saved_builds_repository.rename_build(
        build_id,
        normalized_name,
        profile_id=profile["id"],
    )
    if not updated_build:
        logger.warning(
            "Спроба перейменувати відсутню або недоступну збірку: profile_id=%s build_id=%s",
            profile.get("id"),
            build_id,
        )
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    logger.info(
        "Перейменовано збірку: profile_id=%s build_id=%s new_name=%s",
        profile.get("id"),
        build_id,
        updated_build.get("name"),
    )
    response = RedirectResponse(url="/saved-builds?status=renamed", status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response


@router.post("/saved-builds/{build_id}/delete")
def delete_saved_build(request: Request, build_id: str) -> RedirectResponse:
    profile, _ = _ensure_profile(request)
    deleted_build = saved_builds_repository.delete_build(build_id, profile_id=profile["id"])
    if not deleted_build:
        logger.warning(
            "Спроба видалити відсутню збірку: profile_id=%s build_id=%s",
            profile.get("id"),
            build_id,
        )
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    user_profiles_repository.unlink_saved_build(profile["id"], build_id)
    logger.info(
        "Видалено збережену збірку: profile_id=%s build_id=%s",
        profile.get("id"),
        build_id,
    )
    response = RedirectResponse(url="/saved-builds?status=deleted", status_code=303)
    _set_profile_cookie(
        response,
        profile_id=profile["id"],
        current_cookie=request.cookies.get(PROFILE_COOKIE_NAME),
    )
    return response
