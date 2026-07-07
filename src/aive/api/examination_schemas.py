"""OpenAPI models for forensic examination endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApplyFilterRequest(BaseModel):
    session_id: str = Field(description="Active media session UUID")
    filter_id: str = Field(description="Catalog filter id (e.g. clr_brightness)")
    params: dict[str, Any] | None = Field(default=None, description="Filter-specific parameters")
    insert_at: int | None = Field(
        default=None,
        description="Optional pipeline index; append when omitted",
    )
    replace_filter_prefixes: list[str] | None = Field(
        default=None,
        description="Optional filter id prefixes to ignore during non-destructive preview",
    )
    actor: str = Field(default="examiner", description="Audit trail actor name")


class ResetRequest(BaseModel):
    session_id: str = Field(description="Active media session UUID")


class RemoveFilterRequest(BaseModel):
    session_id: str = Field(description="Active media session UUID")
    index: int = Field(ge=0, description="Zero-based index in the filter pipeline")
    actor: str = Field(default="examiner", description="Audit trail actor name")


class ExaminationPreviewResponse(BaseModel):
    filter_chain: list[str] = Field(description="Applied filter ids in order")
    is_enhanced: bool = Field(description="True when at least one filter is applied")
    time_sec: float = Field(description="Current video playhead time in seconds")
    frame_index: int = Field(description="Current frame index (video)")
    media_type: str = Field(description="Loaded evidence type: image or video")
    source_path: str | None = Field(default=None, description="Path to loaded evidence file")
    preview: str | None = Field(default=None, description="Base64 JPEG of current/enhanced frame")
    preview_original: str | None = Field(default=None, description="Base64 JPEG of non-destructive master")
    width: int | None = Field(default=None, description="Preview width in pixels")
    height: int | None = Field(default=None, description="Preview height in pixels")
    can_undo: bool | None = Field(default=None, description="Whether undo is available")
    can_redo: bool | None = Field(default=None, description="Whether redo is available")
    implemented: bool | None = Field(default=None, description="Whether the filter is implemented")
    preview_only: bool | None = Field(default=None, description="True for non-destructive preview-filter")
    filter_id: str | None = Field(default=None, description="Filter id (preview-filter only)")
    removed_index: int | None = Field(default=None, description="Removed pipeline index")
    removed_filter_id: str | None = Field(default=None, description="Removed filter id")


class LicenseStatusResponse(BaseModel):
    valid: bool
    message: str
    licensed_to: str = ""
    is_trial: bool = False
    days_remaining: int | None = None
    expires: str | None = Field(default=None, description="ISO8601 expiry when licensed")
    machine_id: str = Field(description="Hardware fingerprint for activation")
