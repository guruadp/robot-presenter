import os
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.project import Project, ProjectKnowledgeBase, ProjectSlide
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectSlideOut,
    ProjectSlideScriptOut,
    ProjectUpdate,
    RegenerateScriptRequest,
    ScriptEditRequest,
    ScriptReviewSettingsRequest,
)
from app.services import deck_ingestion, script_generation, slide_vision

router = APIRouter(prefix="/projects", tags=["projects"])

DbDep = Annotated[Session, Depends(get_db)]


def _get_project_or_404(project_id: str, db: Session) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def _get_project_slide_or_404(project: Project, slide_id: str) -> ProjectSlide:
    for slide in project.slides:
        if slide.id == slide_id:
            return slide
    raise HTTPException(404, "Slide not found")


def _get_slide_script_or_404(project: Project, slide_id: str):
    slide = _get_project_slide_or_404(project, slide_id)
    if not slide.script:
        raise HTTPException(404, "Script not found")
    return slide.script


def _mark_stale_scripts_for_kb_changes(project: Project, db: Session) -> None:
    for link in project.knowledge_bases:
        kb = db.get(KnowledgeBase, link.kb_id)
        if not kb:
            continue
        if kb.version != link.pinned_version or kb.content_hash != link.pinned_content_hash:
            reason = f"KB version changed: {kb.name} v{link.pinned_version} -> v{kb.version}"
            for slide in project.slides:
                if slide.script and slide.script.status == "approved":
                    reasons = list(slide.script.stale_reasons or [])
                    if reason not in reasons:
                        slide.script.stale_reasons = [*reasons, reason]
                    slide.script.status = "stale"


def _load_kbs_or_404(kb_ids: list[str], db: Session) -> list[KnowledgeBase]:
    kbs: list[KnowledgeBase] = []
    for kb_id in dict.fromkeys(kb_ids):
        kb = db.get(KnowledgeBase, kb_id)
        if not kb:
            raise HTTPException(404, f"Knowledge base not found: {kb_id}")
        kbs.append(kb)
    return kbs


def _set_project_kbs(project: Project, kb_ids: list[str], db: Session) -> None:
    kbs = _load_kbs_or_404(kb_ids, db)
    project.knowledge_bases = [
        ProjectKnowledgeBase(
            kb_id=kb.id,
            pinned_version=kb.version,
            pinned_content_hash=kb.content_hash,
        )
        for kb in kbs
    ]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: DbDep) -> Project:
    project = Project(
        id=str(uuid.uuid4()),
        name=body.name,
        owner=body.owner,
        tone_profile=body.tone_profile.model_dump(),
    )
    _set_project_kbs(project, body.kb_ids, db)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: DbDep) -> list[Project]:
    projects = db.query(Project).all()
    for project in projects:
        _mark_stale_scripts_for_kb_changes(project, db)
    db.commit()
    return projects


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: DbDep) -> Project:
    project = _get_project_or_404(project_id, db)
    _mark_stale_scripts_for_kb_changes(project, db)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, body: ProjectUpdate, db: DbDep) -> Project:
    project = _get_project_or_404(project_id, db)
    if body.name is not None:
        project.name = body.name
    if body.tone_profile is not None:
        project.tone_profile = body.tone_profile.model_dump()
    if body.kb_ids is not None:
        _set_project_kbs(project, body.kb_ids, db)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: DbDep) -> None:
    project = _get_project_or_404(project_id, db)
    db.delete(project)
    db.commit()


@router.get("/{project_id}/slides", response_model=list[ProjectSlideOut])
def list_slides(project_id: str, db: DbDep) -> list[ProjectSlide]:
    project = _get_project_or_404(project_id, db)
    return project.slides


@router.get("/{project_id}/slides/{slide_id}/image")
def get_slide_image(project_id: str, slide_id: str, db: DbDep) -> FileResponse:
    project = _get_project_or_404(project_id, db)
    slide = _get_project_slide_or_404(project, slide_id)
    if not slide.image_path or not os.path.exists(slide.image_path):
        raise HTTPException(404, "Slide image not found")
    return FileResponse(slide.image_path, media_type="image/png")


@router.post("/{project_id}/scripts", response_model=ProjectOut)
def generate_scripts(project_id: str, db: DbDep) -> Project:
    project = _get_project_or_404(project_id, db)
    if not project.slides:
        raise HTTPException(400, "Upload a deck before generating scripts")

    script_generation.generate_project_scripts(project, db)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.post(
    "/{project_id}/slides/{slide_id}/script/regenerate",
    response_model=ProjectSlideScriptOut,
)
def regenerate_slide_script(
    project_id: str,
    slide_id: str,
    body: RegenerateScriptRequest,
    db: DbDep,
):
    project = _get_project_or_404(project_id, db)
    slide = _get_project_slide_or_404(project, slide_id)
    options = script_generation.GenerationOptions(
        feedback=body.feedback,
        make_shorter=body.make_shorter,
        more_energy=body.more_energy,
        more_citations=body.more_citations,
        tone_override=body.tone_override,
    )
    script = script_generation.regenerate_slide_script(project, slide, db, options)
    db.commit()
    db.refresh(script)
    return script


@router.patch(
    "/{project_id}/slides/{slide_id}/script",
    response_model=ProjectSlideScriptOut,
)
def edit_slide_script(
    project_id: str,
    slide_id: str,
    body: ScriptEditRequest,
    db: DbDep,
):
    project = _get_project_or_404(project_id, db)
    script = _get_slide_script_or_404(project, slide_id)
    if not body.narration.strip():
        raise HTTPException(400, "Narration cannot be empty")
    script_generation.edit_script(script, body.narration)
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post(
    "/{project_id}/slides/{slide_id}/script/revert",
    response_model=ProjectSlideScriptOut,
)
def revert_slide_script(project_id: str, slide_id: str, db: DbDep):
    project = _get_project_or_404(project_id, db)
    script = _get_slide_script_or_404(project, slide_id)
    if not script.revision_history:
        raise HTTPException(400, "No previous script version to revert to")
    script_generation.revert_script(script)
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post(
    "/{project_id}/slides/{slide_id}/script/approve",
    response_model=ProjectSlideScriptOut,
)
def approve_slide_script(project_id: str, slide_id: str, db: DbDep):
    project = _get_project_or_404(project_id, db)
    script = _get_slide_script_or_404(project, slide_id)
    if not script.narration.strip():
        raise HTTPException(400, "Cannot approve an empty script")
    if not script.duration_seconds:
        raise HTTPException(400, "Cannot approve a script without duration")
    script.status = "approved"
    script.stale_reasons = []
    script.approved_at = datetime.now(timezone.utc)
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.patch(
    "/{project_id}/slides/{slide_id}/script/review-settings",
    response_model=ProjectSlideScriptOut,
)
def update_script_review_settings(
    project_id: str,
    slide_id: str,
    body: ScriptReviewSettingsRequest,
    db: DbDep,
):
    project = _get_project_or_404(project_id, db)
    script = _get_slide_script_or_404(project, slide_id)
    script.tone_override = body.tone_override
    script.preview_config = body.preview_config
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post("/{project_id}/deck", response_model=ProjectOut)
async def upload_deck(project_id: str, db: DbDep, file: UploadFile = File(...)) -> Project:
    project = _get_project_or_404(project_id, db)
    filename = file.filename or ""
    if not deck_ingestion.is_pptx(filename, file.content_type):
        raise HTTPException(400, "Only .pptx uploads are supported")

    content = await file.read()
    try:
        parsed_slides = deck_ingestion.parse_pptx(content)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    settings = get_settings()
    project_dir = os.path.join(settings.STORAGE_DIR, "projects", project.id)
    os.makedirs(project_dir, exist_ok=True)
    deck_path = os.path.join(project_dir, "source.pptx")
    with open(deck_path, "wb") as f:
        f.write(content)

    image_dir = os.path.join(project_dir, "slides")
    image_paths = deck_ingestion.render_slide_images(parsed_slides, image_dir, pptx_path=deck_path)

    existing_by_position = {slide.position: slide for slide in project.slides}
    seen_positions = set()
    for parsed_slide, image_path in zip(parsed_slides, image_paths):
        seen_positions.add(parsed_slide.position)
        vision_summary = slide_vision.summarize_slide_image(image_path, parsed_slide)
        existing_slide = existing_by_position.get(parsed_slide.position)
        if existing_slide:
            changed = (
                existing_slide.title != parsed_slide.title
                or existing_slide.body != parsed_slide.body
                or existing_slide.notes != parsed_slide.notes
            )
            existing_slide.title = parsed_slide.title
            existing_slide.body = parsed_slide.body
            existing_slide.notes = parsed_slide.notes
            existing_slide.image_path = image_path
            existing_slide.vision_summary = vision_summary
            existing_slide.generation_context = slide_vision.build_generation_context(
                parsed_slide,
                vision_summary,
            )
            if changed and existing_slide.script:
                existing_slide.script.status = "stale"
                reasons = list(existing_slide.script.stale_reasons or [])
                reason = "Slide content changed after deck upload"
                if reason not in reasons:
                    existing_slide.script.stale_reasons = [*reasons, reason]
        else:
            project.slides.append(
                ProjectSlide(
                    position=parsed_slide.position,
                    title=parsed_slide.title,
                    body=parsed_slide.body,
                    notes=parsed_slide.notes,
                    image_path=image_path,
                    vision_summary=vision_summary,
                    generation_context=slide_vision.build_generation_context(
                        parsed_slide,
                        vision_summary,
                    ),
                ),
            )

    for position, slide in existing_by_position.items():
        if position not in seen_positions:
            db.delete(slide)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project
