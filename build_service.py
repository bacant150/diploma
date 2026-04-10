"""Сумісність зі старими імпортами сервісу побудови."""

from services.build_service import (
    build_configuration_from_form,
    build_option_list,
    build_pc_payload,
    builder_template_context,
    budget_limits_for_purpose,
    default_build_name,
    extract_user_inputs,
    normalize_build_name,
    normalize_purpose,
    result_page_context,
    validate_build_result,
)

__all__ = [
    "build_configuration_from_form",
    "build_option_list",
    "build_pc_payload",
    "builder_template_context",
    "budget_limits_for_purpose",
    "default_build_name",
    "extract_user_inputs",
    "normalize_build_name",
    "normalize_purpose",
    "result_page_context",
    "validate_build_result",
]
