import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base
from app.models import knowledge_base  # noqa: F401
from app.models.project import Project, ProjectSlide, ProjectSlideScript
from app.services.deck_ingestion import ParsedSlide, render_slide_images
from app.services.show_file import (
    PackagingError,
    package_show_file,
    validate_show_bundle,
)
from app.services.tts import OpenAITTS


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_package_show_file_bakes_audio_manifest_and_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_PROVIDER", "free-local")
    get_settings.cache_clear()
    db = _session()
    image_path = render_slide_images(
        [ParsedSlide(1, "Intro", "Explain the program value", "")],
        str(tmp_path),
    )[0]
    project = Project(
        id="p1",
        name="Deck",
        owner="alice",
        tone_profile={"persona": "presenter", "pace": "normal", "formality": "balanced"},
    )
    slide = ProjectSlide(
        id="s1",
        position=1,
        title="Intro",
        body="Explain value",
        notes="",
        image_path=image_path,
        vision_summary="",
        generation_context={},
    )
    ProjectSlideScript(
        slide=slide,
        status="approved",
        narration="Welcome everyone. Today we will make the program value clear.",
        segments=[
            {"index": 1, "text": "Welcome everyone.", "delivery": {}, "audio_tags": ["start"]},
            {
                "index": 2,
                "text": "Today we will make the program value clear.",
                "delivery": {},
                "audio_tags": ["resolve"],
            },
        ],
        citations=[],
        duration_seconds=8,
    )
    project.slides.append(slide)
    db.add(project)
    db.commit()

    show = package_show_file(project)

    assert show.status == "ready"
    assert show.version == 1
    assert os.path.exists(show.manifest_path)
    assert os.path.exists(show.bundle_path)
    assert os.path.getsize(show.bundle_path) > 0
    assert show.manifest["slides"][0]["segments"][0]["audio_path"].endswith(".wav")
    assert validate_show_bundle(os.path.dirname(show.manifest_path), show.manifest) == []
    get_settings.cache_clear()


def test_package_show_file_requires_approved_scripts(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_PROVIDER", "free-local")
    get_settings.cache_clear()


def test_openai_tts_falls_back_after_first_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_TTS_TIMEOUT_SECONDS", "0.01")
    get_settings.cache_clear()

    class BrokenSpeech:
        def create(self, **kwargs):  # noqa: ARG002
            raise RuntimeError("network down")

    class BrokenClient:
        audio = type(
            "Audio",
            (),
            {"speech": type("Speech", (), {"with_streaming_response": BrokenSpeech()})()},
        )()

    monkeypatch.setattr("app.services.tts.OpenAI", lambda **kwargs: BrokenClient())
    tts = OpenAITTS()
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"

    first_result = tts.synthesize("First preview.", str(first))
    second_result = tts.synthesize("Second preview.", str(second))

    assert first_result.provider in {"espeak-ng", "espeak", "dev-wav-placeholder"}
    assert second_result.provider in {"espeak-ng", "espeak", "dev-wav-placeholder"}
    assert first.exists()
    assert second.exists()
    get_settings.cache_clear()
    db = _session()
    image_path = render_slide_images(
        [ParsedSlide(1, "Intro", "Explain the program value", "")],
        str(tmp_path),
    )[0]
    project = Project(id="p1", name="Deck", owner="alice", tone_profile={})
    slide = ProjectSlide(
        id="s1",
        position=1,
        title="Intro",
        body="Explain value",
        notes="",
        image_path=image_path,
        vision_summary="",
        generation_context={},
    )
    ProjectSlideScript(
        slide=slide,
        status="draft",
        narration="Draft narration.",
        segments=[{"index": 1, "text": "Draft narration.", "delivery": {}, "audio_tags": []}],
        citations=[],
        duration_seconds=4,
    )
    project.slides.append(slide)
    db.add(project)
    db.commit()

    try:
        package_show_file(project)
    except PackagingError as exc:
        assert "Slide 1: script must be approved" in exc.errors
    else:
        raise AssertionError("PackagingError was not raised")
    get_settings.cache_clear()
