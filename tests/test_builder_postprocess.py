from __future__ import annotations

from builder_engine.postprocess import finalize_build_result
from parts_db import Part


def _result_from_parts(parts: dict[str, Part]) -> dict[str, object]:
    return {
        "parts": {
            role: {"name": part.name, "price": part.price}
            for role, part in parts.items()
        },
        "notes": [],
        "tier": "mid",
        "total_price": sum(part.price for part in parts.values()),
    }


def test_finalize_build_result_adds_compatibility_and_explanations_for_valid_build() -> None:
    parts = {
        "CPU": Part("cpu", "AMD Ryzen 5 5600G", 7000, {"socket": "AM4", "igpu": True}),
        "Motherboard": Part(
            "mb",
            "B550 (AM4, DDR4, ATX)",
            5000,
            {"socket": "AM4", "ram_type": "DDR4", "wifi": False},
        ),
        "RAM": Part("ram", "DDR4 16GB", 2500, {"ram_type": "DDR4", "size_gb": 16}),
        "SSD": Part("ssd", "SSD 512GB", 2000, {"size_gb": 512}),
        "PSU": Part("psu", "PSU 500W", 2000, {"watt": 500}),
        "Case": Part("case", "Case ATX", 1800, {"size": "ATX", "airflow": True}),
    }

    result = finalize_build_result(
        _result_from_parts(parts),
        parts=parts,
        purpose="office",
        context={"priority": "balanced"},
    )

    assert result["compatibility"]["status"] in {"ok", "warning"}
    assert isinstance(result["compatibility_checks"], list)
    assert any(
        check["code"] == "cpu_socket" and check["status"] == "ok"
        for check in result["compatibility_checks"]
    )
    assert result["part_explanations"]["CPU"]
    assert result["part_explanations"]["PSU"]


def test_finalize_build_result_flags_socket_mismatch_and_weak_psu() -> None:
    parts = {
        "CPU": Part("cpu", "AMD Ryzen 7 9700X", 14000, {"socket": "AM5", "igpu": True}),
        "GPU": Part("gpu", "NVIDIA RTX 5080 16GB", 68000, {"vram": 16}),
        "Motherboard": Part(
            "mb",
            "B760 (LGA1700, DDR5, ATX)",
            8000,
            {"socket": "LGA1700", "ram_type": "DDR5", "wifi": False},
        ),
        "RAM": Part("ram", "DDR5 16GB", 4000, {"ram_type": "DDR5", "size_gb": 16}),
        "SSD": Part("ssd", "SSD 512GB", 2500, {"size_gb": 512}),
        "PSU": Part("psu", "PSU 450W", 1800, {"watt": 450}),
        "Case": Part("case", "Case ATX", 2200, {"size": "ATX", "airflow": True}),
    }

    result = finalize_build_result(
        _result_from_parts(parts),
        parts=parts,
        purpose="gaming",
        context={"resolution": "1440p", "target_fps": 120},
    )

    assert result["compatibility"]["status"] == "error"
    assert any(
        check["code"] == "cpu_socket" and check["status"] == "error"
        for check in result["compatibility_checks"]
    )
    assert any(
        check["code"] == "psu_headroom" and check["status"] == "error"
        for check in result["compatibility_checks"]
    )
    assert result["notes"]
