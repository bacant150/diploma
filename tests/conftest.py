from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def _fake_template_response(template_name: str, context: dict, *args, **kwargs) -> HTMLResponse:
    request = context.get('request')
    path = request.url.path if request else '/'
    html = f"<html><body data-template='{template_name}' data-path='{path}'>ok</body></html>"
    return HTMLResponse(html, status_code=kwargs.get('status_code', 200))


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app_module = importlib.import_module('app')
    web_routes = importlib.import_module('routes.web')
    saved_routes = importlib.import_module('routes.saved_builds')

    monkeypatch.setattr(web_routes.templates, 'TemplateResponse', _fake_template_response)
    monkeypatch.setattr(saved_routes.templates, 'TemplateResponse', _fake_template_response)

    return TestClient(app_module.app)