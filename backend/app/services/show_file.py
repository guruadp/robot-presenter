import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timezone

from app.config import get_settings
from app.models.project import Project, ShowFile
from app.services.tts import get_tts_provider


SHOW_SCHEMA_VERSION = 1


class PackagingError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Show File packaging gate failed")


def validate_packaging_gate(project: Project) -> list[str]:
    errors: list[str] = []
    if not project.slides:
        errors.append("Upload a deck before packaging")

    for slide in project.slides:
        script = slide.script
        label = f"Slide {slide.position}"
        if not script:
            errors.append(f"{label}: missing script")
            continue
        if script.status != "approved":
            errors.append(f"{label}: script must be approved")
        if script.stale_reasons:
            errors.append(f"{label}: script is stale")
        if not script.duration_seconds:
            errors.append(f"{label}: missing duration estimate")
        if _looks_factual(script.narration) and not script.citations:
            errors.append(f"{label}: factual/numeric claims need citations")
        if not script.segments:
            errors.append(f"{label}: missing narration segments")
        if not slide.image_path or not os.path.exists(slide.image_path):
            errors.append(f"{label}: missing rendered slide image")

    return errors


def package_show_file(project: Project) -> ShowFile:
    errors = validate_packaging_gate(project)
    if errors:
        raise PackagingError(errors)

    settings = get_settings()
    show_id = str(uuid.uuid4())
    version = _next_show_version(project)
    show_dir = os.path.join(settings.STORAGE_DIR, "projects", project.id, "show_files", f"v{version}")
    audio_dir = os.path.join(show_dir, "audio")
    slide_dir = os.path.join(show_dir, "slides")
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(slide_dir, exist_ok=True)

    tts = get_tts_provider()
    slides_manifest = []
    providers = set()

    for slide in project.slides:
        assert slide.script is not None
        slide_image_name = f"slide_{slide.position}.png"
        bundled_slide_path = os.path.join(slide_dir, slide_image_name)
        shutil.copyfile(slide.image_path, bundled_slide_path)

        segment_manifests = []
        voice_id = _voice_for(project, slide.script)
        for segment in slide.script.segments:
            audio_name = f"slide_{slide.position}_segment_{segment['index']}.wav"
            audio_path = os.path.join(audio_dir, audio_name)
            result = tts.synthesize(
                text=segment["text"],
                output_path=audio_path,
                voice_id=voice_id,
                preview_config=slide.script.preview_config,
            )
            providers.add(result.provider)
            segment_manifests.append(
                {
                    "index": segment["index"],
                    "text": segment["text"],
                    "delivery": segment.get("delivery", {}),
                    "audio_tags": segment.get("audio_tags", []),
                    "audio_path": os.path.relpath(audio_path, show_dir),
                    "audio_duration_seconds": result.duration_seconds,
                    "voice_id": result.voice_id,
                    "gesture_cue": None,
                }
            )

        slides_manifest.append(
            {
                "slide_id": slide.id,
                "position": slide.position,
                "title": slide.title,
                "image_path": os.path.relpath(bundled_slide_path, show_dir),
                "script_version": slide.script.version,
                "duration_seconds": slide.script.duration_seconds,
                "citations": slide.script.citations,
                "segments": segment_manifests,
            }
        )

    manifest = {
        "schema_version": SHOW_SCHEMA_VERSION,
        "id": show_id,
        "project_id": project.id,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tts_provider": ", ".join(sorted(providers)) or tts.provider_name,
        "voice_config": project.tone_profile,
        "kb_pointers": [
            {
                "kb_id": link.kb_id,
                "pinned_version": link.pinned_version,
                "pinned_content_hash": link.pinned_content_hash,
            }
            for link in project.knowledge_bases
        ],
        "slides": slides_manifest,
    }

    manifest_path = os.path.join(show_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    validation_errors = validate_show_bundle(show_dir, manifest)
    status = "ready" if not validation_errors else "invalid"
    bundle_path = os.path.join(show_dir, f"ednex_show_v{version}.zip")
    _zip_show_dir(show_dir, bundle_path)

    return ShowFile(
        id=show_id,
        project_id=project.id,
        version=version,
        status=status,
        manifest_path=manifest_path,
        bundle_path=bundle_path,
        manifest=manifest,
        validation_errors=validation_errors,
        tts_provider=manifest["tts_provider"],
    )


def validate_show_bundle(show_dir: str, manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != SHOW_SCHEMA_VERSION:
        errors.append("Unsupported Show File schema version")
    if not manifest.get("slides"):
        errors.append("Show File contains no slides")

    for slide in manifest.get("slides", []):
        image_path = os.path.join(show_dir, slide.get("image_path", ""))
        if not os.path.exists(image_path):
            errors.append(f"Slide {slide.get('position')}: missing bundled image")
        for segment in slide.get("segments", []):
            audio_path = os.path.join(show_dir, segment.get("audio_path", ""))
            if not os.path.exists(audio_path):
                errors.append(f"Slide {slide.get('position')} segment {segment.get('index')}: missing audio")
            elif os.path.getsize(audio_path) <= 44:
                errors.append(f"Slide {slide.get('position')} segment {segment.get('index')}: empty audio")

    return errors


def _next_show_version(project: Project) -> int:
    versions = [show.version for show in project.show_files]
    return max(versions, default=0) + 1


def _voice_for(project: Project, script) -> str | None:
    return (
        script.preview_config.get("voice_id")
        or script.tone_override.get("voice_id")
        or (project.tone_profile or {}).get("voice_id")
    )


def _looks_factual(text: str) -> bool:
    return any(char.isdigit() for char in text) or "$" in text or "%" in text


def _zip_show_dir(show_dir: str, bundle_path: str) -> None:
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(show_dir):
            for filename in files:
                path = os.path.join(root, filename)
                if path == bundle_path:
                    continue
                zf.write(path, os.path.relpath(path, show_dir))
