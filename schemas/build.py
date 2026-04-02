from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

PurposeLiteral = Literal["gaming", "office", "study", "creator"]
BudgetModeLiteral = Literal["manual", "auto"]
ResolutionLiteral = Literal["1080p", "1440p", "4k"]
GraphicsQualityLiteral = Literal["low", "medium", "high", "ultra"]
GpuModeLiteral = Literal["auto", "dedicated", "integrated"]
CpuBrandLiteral = Literal["auto", "amd", "intel"]
GpuBrandLiteral = Literal["auto", "amd", "nvidia"]
MemoryPlatformLiteral = Literal["auto", "ddr4", "ddr5"]
PriorityLiteral = Literal["budget", "balanced", "best"]
TabsLiteral = Literal["auto", "up_to_10", "10_30", "30_60", "60_plus"]
MonitorsLiteral = Literal["auto", "1", "2", "3_plus"]
CreatorComplexityLiteral = Literal["auto", "light", "medium", "heavy"]
RamSizeLiteral = Literal["auto", "2", "4", "8", "16", "32", "64", "96", "128", "192", "256"]
SsdSizeLiteral = Literal["auto", "128", "256", "512", "1000", "2000", "4000", "8000"]

PURPOSE_VALUES = {"gaming", "office", "study", "creator"}
BUDGET_MODE_VALUES = {"manual", "auto"}
RESOLUTION_VALUES = {"1080p", "1440p", "4k"}
GRAPHICS_QUALITY_VALUES = {"low", "medium", "high", "ultra"}
GPU_MODE_VALUES = {"auto", "dedicated", "integrated"}
CPU_BRAND_VALUES = {"auto", "amd", "intel"}
GPU_BRAND_VALUES = {"auto", "amd", "nvidia"}
MEMORY_PLATFORM_VALUES = {"auto", "ddr4", "ddr5"}
PRIORITY_VALUES = {"budget", "balanced", "best"}
TABS_VALUES = {"auto", "up_to_10", "10_30", "30_60", "60_plus"}
MONITORS_VALUES = {"auto", "1", "2", "3_plus"}
CREATOR_COMPLEXITY_VALUES = {"auto", "light", "medium", "heavy"}
RAM_SIZE_VALUES = {"auto", "2", "4", "8", "16", "32", "64", "96", "128", "192", "256"}
SSD_SIZE_VALUES = {"auto", "128", "256", "512", "1000", "2000", "4000", "8000"}


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default



def _unique_str_list(values: Any) -> list[str]:
    if values is None:
        return []

    if isinstance(values, str):
        raw_items: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        raw_items = values
    else:
        raw_items = [values]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return normalized


class PurposeDetectionFormSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    description: str = Field(min_length=8, max_length=1000)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: Any) -> str:
        return str(value or "").strip()


class BuildInputsSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    budget_mode: BudgetModeLiteral = "manual"
    budget: int = 0
    purpose: PurposeLiteral = "gaming"
    resolution: ResolutionLiteral = "1080p"
    wifi: bool = False
    games: list[str] = Field(default_factory=list)
    graphics_quality: GraphicsQualityLiteral = "high"
    target_fps: int = 60
    gpu_mode: GpuModeLiteral = "auto"
    cpu_brand: CpuBrandLiteral = "auto"
    gpu_brand: GpuBrandLiteral = "auto"
    ram_size: RamSizeLiteral = "auto"
    ssd_size: SsdSizeLiteral = "auto"
    memory_platform: MemoryPlatformLiteral = "auto"
    office_apps: list[str] = Field(default_factory=list)
    office_tabs: TabsLiteral = "auto"
    office_monitors: MonitorsLiteral = "auto"
    study_apps: list[str] = Field(default_factory=list)
    study_tabs: TabsLiteral = "auto"
    study_monitors: MonitorsLiteral = "auto"
    creator_apps: list[str] = Field(default_factory=list)
    creator_complexity: CreatorComplexityLiteral = "auto"
    creator_monitors: MonitorsLiteral = "auto"
    priority: PriorityLiteral = "balanced"

    @field_validator("budget", mode="before")
    @classmethod
    def normalize_budget(cls, value: Any) -> int:
        return _safe_int(value, 0)

    @field_validator("target_fps", mode="before")
    @classmethod
    def normalize_target_fps(cls, value: Any) -> int:
        return _safe_int(value, 60)

    @field_validator("wifi", mode="before")
    @classmethod
    def normalize_wifi(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value or "no").strip().lower() in {"yes", "true", "1", "on"}

    @field_validator("games", "office_apps", "study_apps", "creator_apps", mode="before")
    @classmethod
    def normalize_str_list(cls, value: Any) -> list[str]:
        return _unique_str_list(value)

    @field_validator("budget_mode", mode="before")
    @classmethod
    def normalize_budget_mode(cls, value: Any) -> str:
        normalized = str(value or "manual").strip().lower()
        return normalized if normalized in BUDGET_MODE_VALUES else "manual"

    @field_validator("purpose", mode="before")
    @classmethod
    def normalize_purpose(cls, value: Any) -> str:
        normalized = str(value or "gaming").strip().lower()
        return normalized if normalized in PURPOSE_VALUES else "gaming"

    @field_validator("resolution", mode="before")
    @classmethod
    def normalize_resolution(cls, value: Any) -> str:
        normalized = str(value or "1080p").strip().lower()
        return normalized if normalized in RESOLUTION_VALUES else "1080p"

    @field_validator("graphics_quality", mode="before")
    @classmethod
    def normalize_graphics_quality(cls, value: Any) -> str:
        normalized = str(value or "high").strip().lower()
        return normalized if normalized in GRAPHICS_QUALITY_VALUES else "high"

    @field_validator("gpu_mode", mode="before")
    @classmethod
    def normalize_gpu_mode(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in GPU_MODE_VALUES else "auto"

    @field_validator("cpu_brand", mode="before")
    @classmethod
    def normalize_cpu_brand(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in CPU_BRAND_VALUES else "auto"

    @field_validator("gpu_brand", mode="before")
    @classmethod
    def normalize_gpu_brand(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in GPU_BRAND_VALUES else "auto"

    @field_validator("ram_size", mode="before")
    @classmethod
    def normalize_ram_size(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in RAM_SIZE_VALUES else "auto"

    @field_validator("ssd_size", mode="before")
    @classmethod
    def normalize_ssd_size(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in SSD_SIZE_VALUES else "auto"

    @field_validator("memory_platform", mode="before")
    @classmethod
    def normalize_memory_platform(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in MEMORY_PLATFORM_VALUES else "auto"

    @field_validator("office_tabs", "study_tabs", mode="before")
    @classmethod
    def normalize_tabs(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in TABS_VALUES else "auto"

    @field_validator("office_monitors", "study_monitors", "creator_monitors", mode="before")
    @classmethod
    def normalize_monitors(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in MONITORS_VALUES else "auto"

    @field_validator("creator_complexity", mode="before")
    @classmethod
    def normalize_creator_complexity(cls, value: Any) -> str:
        normalized = str(value or "auto").strip().lower()
        return normalized if normalized in CREATOR_COMPLEXITY_VALUES else "auto"

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> str:
        normalized = str(value or "balanced").strip().lower()
        return normalized if normalized in PRIORITY_VALUES else "balanced"

    @model_validator(mode="after")
    def apply_runtime_constraints(self, info: ValidationInfo) -> "BuildInputsSchema":
        context = info.context or {}
        budget_limits = context.get("budget_limits") or {"min": 15000, "max": 150000}
        fps_limits = context.get("fps_limits") or {"min": 30, "max": 500}

        if self.budget_mode == "auto":
            self.budget = 0
        else:
            self.budget = max(int(budget_limits["min"]), min(int(budget_limits["max"]), self.budget))

        self.target_fps = max(int(fps_limits["min"]), min(int(fps_limits["max"]), self.target_fps))

        if self.purpose != "gaming":
            self.games = []
            self.graphics_quality = "high"
            self.target_fps = 60

        if self.purpose not in {"gaming", "creator"}:
            self.gpu_brand = "auto"
            self.resolution = "1080p"

        if self.purpose != "office":
            self.office_apps = []
            self.office_tabs = "auto"
            self.office_monitors = "auto"

        if self.purpose != "study":
            self.study_apps = []
            self.study_tabs = "auto"
            self.study_monitors = "auto"

        if self.purpose != "creator":
            self.creator_apps = []
            self.creator_complexity = "auto"
            self.creator_monitors = "auto"

        return self


class BuildInputsViewSchema(BuildInputsSchema):
    games_titles: list[str] = Field(default_factory=list)
    office_apps_titles: list[str] = Field(default_factory=list)
    study_apps_titles: list[str] = Field(default_factory=list)
    creator_apps_titles: list[str] = Field(default_factory=list)

    @field_validator("games_titles", "office_apps_titles", "study_apps_titles", "creator_apps_titles", mode="before")
    @classmethod
    def normalize_title_lists(cls, value: Any) -> list[str]:
        return _unique_str_list(value)


class BuildPayloadSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget: int
    purpose: PurposeLiteral
    resolution: ResolutionLiteral
    wifi: bool
    games: list[str] = Field(default_factory=list)
    graphics_quality: GraphicsQualityLiteral
    target_fps: int
    gpu_mode: GpuModeLiteral
    cpu_brand: CpuBrandLiteral
    gpu_brand: GpuBrandLiteral
    ram_size: RamSizeLiteral
    ssd_size: SsdSizeLiteral
    memory_platform: MemoryPlatformLiteral
    office_apps: list[str] = Field(default_factory=list)
    office_tabs: TabsLiteral
    office_monitors: MonitorsLiteral
    study_apps: list[str] = Field(default_factory=list)
    study_tabs: TabsLiteral
    study_monitors: MonitorsLiteral
    creator_apps: list[str] = Field(default_factory=list)
    creator_project_complexity: CreatorComplexityLiteral
    creator_monitors: MonitorsLiteral
    priority: PriorityLiteral

    @classmethod
    def from_inputs(cls, inputs: BuildInputsSchema | BuildInputsViewSchema | dict[str, Any]) -> "BuildPayloadSchema":
        source = inputs.model_dump(mode="json") if isinstance(inputs, BaseModel) else dict(inputs)
        return cls.model_validate(
            {
                "budget": source.get("budget", 0),
                "purpose": source.get("purpose", "gaming"),
                "resolution": source.get("resolution", "1080p"),
                "wifi": source.get("wifi", False),
                "games": source.get("games", []),
                "graphics_quality": source.get("graphics_quality", "high"),
                "target_fps": source.get("target_fps", 60),
                "gpu_mode": source.get("gpu_mode", "auto"),
                "cpu_brand": source.get("cpu_brand", "auto"),
                "gpu_brand": source.get("gpu_brand", "auto"),
                "ram_size": source.get("ram_size", "auto"),
                "ssd_size": source.get("ssd_size", "auto"),
                "memory_platform": source.get("memory_platform", "auto"),
                "office_apps": source.get("office_apps", []),
                "office_tabs": source.get("office_tabs", "auto"),
                "office_monitors": source.get("office_monitors", "auto"),
                "study_apps": source.get("study_apps", []),
                "study_tabs": source.get("study_tabs", "auto"),
                "study_monitors": source.get("study_monitors", "auto"),
                "creator_apps": source.get("creator_apps", []),
                "creator_project_complexity": source.get("creator_complexity", "auto"),
                "creator_monitors": source.get("creator_monitors", "auto"),
                "priority": source.get("priority", "balanced"),
            }
        )


class BuildPartSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    price: int | float | None = None
    description: str | None = None
    image: str | None = None
    image_filename: str | None = None


class BuildAlternativeCardSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    is_primary: bool | None = None
    label: str | None = None
    name: str | None = None
    total_price: int | float | None = None
    parts: dict[str, BuildPartSchema] | list[BuildPartSchema] | None = None

    @field_validator("parts", mode="before")
    @classmethod
    def normalize_parts(cls, value: Any) -> dict[str, Any] | list[Any] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            return value
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return list(value)
        return None
    result_payload: dict[str, Any] | None = None


class BuildResultSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    tier: str | None = None
    total_price: int | float | None = None
    recommended_budget: int | float | None = None
    parts: dict[str, BuildPartSchema] = Field(default_factory=dict)
    alternatives: list[BuildAlternativeCardSchema] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SavedBuildRecordSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str
    profile_id: str | None = None
    query_id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    saved_at: datetime
    inputs: BuildInputsViewSchema
    result: BuildResultSchema

    @field_validator("id", "profile_id", "query_id", mode="before")
    @classmethod
    def normalize_ids(cls, value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any) -> str:
        return str(value or "").strip()


class QueryResultSummarySchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tier: str | None = None
    total_price: int | float | None = None
    recommended_budget: int | float | None = None
    parts_count: int = 0


class QueryHistoryRecordSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str
    created_at: datetime
    source: str = "builder_form"
    inputs: BuildInputsViewSchema
    result_summary: QueryResultSummarySchema
    result_snapshot: BuildResultSchema | None = None
    saved_build_id: str | None = None

    @field_validator("id", "source", "saved_build_id", mode="before")
    @classmethod
    def normalize_query_strings(cls, value: Any) -> str | None:
        text = str(value or "").strip()
        return text or None


class UserProfileRecordSchema(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: str
    name: str = Field(min_length=1, max_length=120)
    created_at: datetime
    last_seen_at: datetime
    saved_build_ids: list[str] = Field(default_factory=list)
    query_history: list[QueryHistoryRecordSchema] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def normalize_profile_id(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("name", mode="before")
    @classmethod
    def normalize_profile_name(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("saved_build_ids", mode="before")
    @classmethod
    def normalize_saved_build_ids(cls, value: Any) -> list[str]:
        return _unique_str_list(value)
