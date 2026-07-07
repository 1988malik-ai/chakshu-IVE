"""AI/ML enhancement API — tools, ONNX import, session apply (R-090, R-091)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from aive.ai.enhance import BUILTIN_TOOLS, list_tools, onnx_runtime_available, run_ai_tool
from aive.ai.models import get_registry
from aive.api.examination_payload import examination_preview_fields
from aive.api.session import sessions
from aive.forensics.audit import audit_log

router = APIRouter(prefix="/api/ai", tags=["ai"])


class EnhanceSessionBody(BaseModel):
    session_id: str
    tool: str = "auto_enhance"
    model_id: str = ""
    strength: float = Field(default=1.0, ge=0.1, le=3.0)
    actor: str = "examiner"
    add_to_pipeline: bool = True


class ImportPathBody(BaseModel):
    path: str
    model_id: str = ""
    name: str = ""
    task: str = "enhance"
    description: str = ""
    input_width: int = 256
    input_height: int = 256


class UpdateModelBody(BaseModel):
    name: str | None = None
    task: str | None = None
    description: str | None = None


@router.get("/status")
def ai_status() -> dict[str, Any]:
    reg = get_registry()
    st = reg.status()
    st["builtin_tools"] = len(BUILTIN_TOOLS)
    st["onnxruntime_available"] = onnx_runtime_available()
    return st


@router.get("/tools")
def ai_tools() -> dict[str, Any]:
    return {"tools": list_tools(), "builtin": list(BUILTIN_TOOLS.keys())}


@router.get("/models")
def ai_models() -> dict[str, Any]:
    reg = get_registry()
    return {
        "models": [m.to_dict() for m in reg.list_models()],
        "models_dir": str(reg.models_dir),
    }


@router.post("/models/import")
async def import_model_upload(
    file: UploadFile = File(...),
    model_id: str = "",
    name: str = "",
    task: str = "enhance",
    description: str = "",
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".onnx"):
        raise HTTPException(400, "Upload a .onnx model file")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    reg = get_registry()
    tmp = reg.models_dir / f"_upload_{file.filename}"
    tmp.write_bytes(data)
    info = None
    try:
        info = reg.import_model(
            tmp,
            model_id=model_id or None,
            name=name or None,
            task=task,
            description=description,
        )
    except ValueError as e:
        tmp.unlink(missing_ok=True)
        raise HTTPException(400, str(e)) from e
    finally:
        if tmp.exists() and (info is None or info.path.resolve() != tmp.resolve()):
            tmp.unlink(missing_ok=True)
    audit_log.record("ai", "MODEL_IMPORT", "examiner", model_id=info.id)
    return {"success": True, "model": info.to_dict()}


@router.post("/models/import-path")
def import_model_path(body: ImportPathBody) -> dict[str, Any]:
    p = Path(body.path).expanduser()
    reg = get_registry()
    try:
        info = reg.import_model(
            p,
            model_id=body.model_id or None,
            name=body.name or None,
            task=body.task,
            input_size=(body.input_width, body.input_height),
            description=body.description,
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"success": True, "model": info.to_dict()}


@router.delete("/models/{model_id}")
def delete_model(model_id: str) -> dict[str, Any]:
    reg = get_registry()
    if not reg.delete_model(model_id):
        raise HTTPException(404, "Model not found")
    return {"success": True, "deleted": model_id}


@router.post("/enhance/session")
def enhance_session(body: EnhanceSessionBody) -> dict[str, Any]:
    session = sessions.get(body.session_id)
    if not session or session.master_frame is None:
        raise HTTPException(400, "No media loaded in session")

    params = {
        "tool": body.tool,
        "model_id": body.model_id,
        "strength": body.strength,
    }
    filter_id = "both_enhance_ai"
    if body.tool == "denoise_ai":
        filter_id = "both_denoise_ai"
    elif body.tool == "deblur_ai":
        filter_id = "both_deblur_ai"
    elif body.tool == "super_resolution":
        filter_id = "both_upscale_ai" if session.media_type == "video" else "rst_super_resolution"

    if body.add_to_pipeline:
        sessions.apply_filter(body.session_id, filter_id, params)
        session = sessions.get(body.session_id)
    else:
        session.undo.push(session.frame, "ai_enhance")
        session.frame = run_ai_tool(session.frame, params)

    audit_log.record(
        session.id,
        "AI_ENHANCE",
        body.actor,
        tool=body.tool,
        model_id=body.model_id,
    )
    return {
        "success": True,
        "tool": body.tool,
        "model_id": body.model_id,
        **examination_preview_fields(session),
    }
