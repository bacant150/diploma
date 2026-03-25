from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import FPS_LIMITS, STATUS_MESSAGES, TEMPLATES_DIR
from repositories.saved_builds_repository import saved_builds_repository
from schemas import BuildInputsViewSchema, BuildResultSchema, SavedBuildRecordSchema
from services.build_service import budget_limits_for_purpose, normalize_build_name, result_page_context
from utils.assets import attach_part_images
from utils.validation import extract_json_object

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()


@router.get('/saved-builds', response_class=HTMLResponse)
def saved_builds_page(request: Request) -> HTMLResponse:
    status = request.query_params.get('status', '')
    saved_builds = [saved_builds_repository.prepare_for_list(build) for build in reversed(saved_builds_repository.load_all())]
    return templates.TemplateResponse(
        'saved-builds.html',
        {
            'request': request,
            'saved_builds': saved_builds,
            'status_message': STATUS_MESSAGES.get(status, ''),
        },
    )


@router.get('/saved-builds/view', response_class=HTMLResponse)
def saved_build_view_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse('saved-build-view.html', {'request': request})


@router.post('/saved-builds/save')
async def save_build(request: Request) -> RedirectResponse:
    form = await request.form()
    raw_inputs = extract_json_object(form.get('inputs_json', '{}'), field_name='inputs_json')
    raw_result = extract_json_object(form.get('result_json', '{}'), field_name='result_json')

    purpose = str(raw_inputs.get('purpose', 'gaming') or 'gaming')
    budget_limits = budget_limits_for_purpose(purpose)
    inputs = BuildInputsViewSchema.model_validate(
        raw_inputs,
        context={'budget_limits': budget_limits, 'fps_limits': FPS_LIMITS},
    ).model_dump(mode='json')
    result = BuildResultSchema.model_validate(raw_result).model_dump(mode='json')

    build_name = normalize_build_name(str(form.get('build_name', '')), inputs)

    saved_builds = saved_builds_repository.load_all()
    saved_builds.append(
        SavedBuildRecordSchema.model_validate(
            {
                'id': __import__('uuid').uuid4().hex,
                'name': build_name,
                'saved_at': datetime.now().isoformat(timespec='seconds'),
                'inputs': inputs,
                'result': result,
            }
        ).model_dump(mode='json')
    )
    saved_builds_repository.write_all(saved_builds)
    return RedirectResponse(url='/saved-builds?status=saved', status_code=303)


@router.get('/saved-builds/{build_id}', response_class=HTMLResponse)
def open_saved_build(request: Request, build_id: str) -> HTMLResponse:
    saved_build = saved_builds_repository.find_by_id(build_id)
    if not saved_build:
        raise HTTPException(status_code=404, detail='Збірку не знайдено.')

    inputs = saved_build.get('inputs', {})
    result = attach_part_images(saved_build.get('result', {}))
    return templates.TemplateResponse(
        'result.html',
        result_page_context(request, inputs, result, saved_build_name=saved_build.get('name')),
    )


@router.post('/saved-builds/{build_id}/rename')
def rename_saved_build(build_id: str, build_name: str = Form(...)) -> RedirectResponse:
    saved_builds = saved_builds_repository.load_all()
    for build in saved_builds:
        if build.get('id') == build_id:
            build['name'] = normalize_build_name(build_name, build.get('inputs', {}))
            saved_builds_repository.write_all(saved_builds)
            return RedirectResponse(url='/saved-builds?status=renamed', status_code=303)
    raise HTTPException(status_code=404, detail='Збірку не знайдено.')


@router.post('/saved-builds/{build_id}/delete')
def delete_saved_build(build_id: str) -> RedirectResponse:
    saved_builds = saved_builds_repository.load_all()
    filtered_builds = [build for build in saved_builds if build.get('id') != build_id]
    if len(filtered_builds) == len(saved_builds):
        raise HTTPException(status_code=404, detail='Збірку не знайдено.')

    saved_builds_repository.write_all(filtered_builds)
    return RedirectResponse(url='/saved-builds?status=deleted', status_code=303)
