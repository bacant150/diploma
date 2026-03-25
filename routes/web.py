from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from config import SHOW_DEBUG_ROUTES, STATIC_DIR, TEMPLATES_DIR
from services.ai_service import (
    build_choose_purpose_context,
    detect_purpose_from_description,
    get_ai_health_status,
)
from services.build_service import build_configuration_from_form, builder_template_context, result_page_context

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get('/', response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse('landing.html', {'request': request})


@router.get('/choose-purpose', response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    return templates.TemplateResponse('choose-purpose.html', build_choose_purpose_context(request))


@router.post('/detect-purpose', response_class=JSONResponse)
async def detect_purpose(request: Request) -> JSONResponse:
    form = await request.form()
    payload, status_code = detect_purpose_from_description(form.get('description', ''))
    return JSONResponse(payload, status_code=status_code)


@router.get('/health/ai', response_class=JSONResponse)
def ai_health() -> JSONResponse:
    status = get_ai_health_status(probe=True)
    return JSONResponse(status, status_code=200 if status.get('available') else 503)


@router.get('/builder/{purpose}', response_class=HTMLResponse)
def builder_page(request: Request, purpose: str) -> HTMLResponse:
    context = {'request': request, **builder_template_context(purpose)}
    return templates.TemplateResponse('index.html', context)


@router.post('/build', response_class=HTMLResponse)
async def build(request: Request) -> HTMLResponse:
    form = await request.form()
    inputs, result = build_configuration_from_form(form)
    return templates.TemplateResponse('result.html', result_page_context(request, inputs, result))


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
