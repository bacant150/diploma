from __future__ import annotations

import logging
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
from utils.profile_cookie import PROFILE_COOKIE_NAME, ensure_profile, set_profile_cookie

logger = logging.getLogger('pcbuilder.routes.web')
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


@router.get('/', response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    profile, _ = ensure_profile(request, repository=user_profiles_repository, logger=logger)
    response = templates.TemplateResponse('landing.html', {'request': request})
    set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.get('/choose-purpose', response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    profile, _ = ensure_profile(request, repository=user_profiles_repository, logger=logger)
    logger.info(
        'Відкрито сторінку вибору призначення ПК: profile_id=%s client_ip=%s',
        profile.get('id'),
        _client_ip(request),
    )
    response = templates.TemplateResponse('choose-purpose.html', build_choose_purpose_context(request))
    set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.post('/detect-purpose', response_class=JSONResponse)
async def detect_purpose(request: Request) -> JSONResponse:
    form = await request.form()
    description = str(form.get('description', '') or '')
    payload, status_code = detect_purpose_from_description(description)

    profile, _ = ensure_profile(request, repository=user_profiles_repository, logger=logger)
    logger.info(
        'Запит AI-визначення сценарію: profile_id=%s status=%s accepted=%s purpose=%s confidence=%s text_len=%s client_ip=%s',
        profile.get('id'),
        status_code,
        payload.get('accepted'),
        payload.get('purpose') or payload.get('purpose_title'),
        payload.get('confidence_percent'),
        len(description),
        _client_ip(request),
    )

    response = JSONResponse(payload, status_code=status_code)
    set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.get('/health/ai', response_class=JSONResponse)
def ai_health() -> JSONResponse:
    status = get_ai_health_status(probe=True)
    available = bool(status.get('available'))
    logger.info('Перевірка AI health: available=%s loaded=%s', available, status.get('loaded'))
    return JSONResponse(status, status_code=200 if available else 503)


@router.get('/builder/{purpose}', response_class=HTMLResponse)
def builder_page(request: Request, purpose: str) -> HTMLResponse:
    profile, _ = ensure_profile(request, repository=user_profiles_repository, logger=logger)
    logger.info(
        'Відкрито конфігуратор: purpose=%s profile_id=%s client_ip=%s',
        purpose,
        profile.get('id'),
        _client_ip(request),
    )
    context = {'request': request, **builder_template_context(purpose)}
    response = templates.TemplateResponse('index.html', context)
    set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
    return response


@router.post('/build', response_class=HTMLResponse)
async def build(request: Request) -> HTMLResponse:
    form = await request.form()
    profile, _ = ensure_profile(request, repository=user_profiles_repository, logger=logger)

    logger.info(
        'Початок побудови конфігурації: profile_id=%s purpose=%s budget_mode=%s client_ip=%s',
        profile.get('id'),
        form.get('purpose', 'gaming'),
        form.get('budget_mode', 'manual'),
        _client_ip(request),
    )

    inputs, result = build_configuration_from_form(form)
    query_entry = user_profiles_repository.add_query(profile['id'], inputs, result)

    logger.info(
        'Конфігурацію успішно побудовано: profile_id=%s query_id=%s purpose=%s tier=%s total=%s alternatives=%s',
        profile.get('id'),
        query_entry.get('id'),
        inputs.get('purpose'),
        result.get('tier'),
        result.get('total') or result.get('total_price'),
        len(result.get('alternatives', []) or []),
    )

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
    set_profile_cookie(response, profile_id=profile['id'], current_cookie=request.cookies.get(PROFILE_COOKIE_NAME))
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
