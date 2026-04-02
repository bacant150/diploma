from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from config import SHOW_DEBUG_ROUTES, STATIC_DIR, TEMPLATES_DIR
from repositories.user_profiles_repository import user_profiles_repository
from services.ai_service import (
    build_choose_purpose_context,
    detect_purpose_from_description,
    get_ai_health_status,
)
from services.build_service import build_configuration_from_form, builder_template_context, result_page_context

PROFILE_COOKIE_NAME = 'pcoll_profile_id'
PROFILE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


def _ensure_profile(request: Request) -> tuple[dict, bool]:
    return user_profiles_repository.get_or_create(request.cookies.get(PROFILE_COOKIE_NAME))


def _set_profile_cookie(response: HTMLResponse | JSONResponse, *, profile_id: str, current_cookie: str | None) -> None:
    if str(current_cookie or '').strip() == str(profile_id or '').strip():
        return
    response.set_cookie(
        PROFILE_COOKIE_NAME,
        profile_id,
        max_age=PROFILE_COOKIE_MAX_AGE,
        httponly=False,
        samesite='lax',
    )


@router.get('/', response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    profile, _ = _ensure_profile(request)
    response = templates.TemplateResponse('landing.html', {'request': request})
    _set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.get('/choose-purpose', response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    profile, _ = _ensure_profile(request)
    response = templates.TemplateResponse('choose-purpose.html', build_choose_purpose_context(request))
    _set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.post('/detect-purpose', response_class=JSONResponse)
async def detect_purpose(request: Request) -> JSONResponse:
    form = await request.form()
    payload, status_code = detect_purpose_from_description(form.get('description', ''))
    response = JSONResponse(payload, status_code=status_code)
    profile, _ = _ensure_profile(request)
    _set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.get('/health/ai', response_class=JSONResponse)
def ai_health() -> JSONResponse:
    status = get_ai_health_status(probe=True)
    return JSONResponse(status, status_code=200 if status.get('available') else 503)


@router.get('/builder/{purpose}', response_class=HTMLResponse)
def builder_page(request: Request, purpose: str) -> HTMLResponse:
    profile, _ = _ensure_profile(request)
    context = {'request': request, **builder_template_context(purpose)}
    response = templates.TemplateResponse('index.html', context)
    _set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.post('/build', response_class=HTMLResponse)
async def build(request: Request) -> HTMLResponse:
    form = await request.form()
    inputs, result = build_configuration_from_form(form)

    profile, _ = _ensure_profile(request)
    query_entry = user_profiles_repository.add_query(profile['id'], inputs, result)

    response = templates.TemplateResponse(
        'result.html',
        result_page_context(
            request,
            inputs,
            result,
            profile_query_id=query_entry.get('id'),
            profile_name=profile.get('name'),
        ),
    )
    _set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


if SHOW_DEBUG_ROUTES:
    @router.get('/debug-paths', response_class=PlainTextResponse)
    def debug_paths() -> str:
        return (
            f"APP FILE: {Path(__file__).resolve()}\n"
            f"ROUTES DIR: {Path(__file__).resolve().parent}\n"
            f"STATIC_DIR: {STATIC_DIR}\n"
            f"STYLE_CSS: {STATIC_DIR / 'style.css'}\n"
            f"TEMPLATES_DIR: {TEMPLATES_DIR}\n"
            f"CHOOSE_TEMPLATE: {TEMPLATES_DIR / 'choose-purpose.html'}\n"
        )
