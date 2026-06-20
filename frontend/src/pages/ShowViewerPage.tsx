import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  ScreenShare,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { projectApi } from "../api/projects";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";

interface ShowSlide {
  slide_id: string;
  position: number;
  title: string | null;
  image_path: string;
  duration_seconds: number;
  segments: Array<{
    index: number;
    text: string;
    audio_path?: string;
  }>;
}

interface RenderEvent {
  type: "render_done";
  slide: number;
  at: string;
}

export default function ShowViewerPage() {
  const { projectId, showFileId } = useParams<{
    projectId: string;
    showFileId: string;
  }>();
  const navigate = useNavigate();
  const [index, setIndex] = useState(0);
  const [jumpStack, setJumpStack] = useState<number[]>([]);
  const [events, setEvents] = useState<RenderEvent[]>([]);

  const { data: showFile, isLoading } = useQuery({
    queryKey: ["show-file", projectId, showFileId],
    queryFn: () => projectApi.getShowFile(projectId!, showFileId!),
    enabled: !!projectId && !!showFileId,
  });

  const slides = useMemo(
    () => ((showFile?.manifest.slides as ShowSlide[] | undefined) ?? []),
    [showFile]
  );
  const current = slides[index] ?? null;

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === "PageDown") next();
      if (e.key === "ArrowLeft" || e.key === "PageUp") prev();
      if (e.key === "Escape") navigate(`/projects/${projectId}`);
      if (e.key === "b") jumpBack();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  });

  function goto(nextIndex: number, pushCurrent = true) {
    if (nextIndex < 0 || nextIndex >= slides.length || nextIndex === index) return;
    if (pushCurrent) setJumpStack((stack) => [...stack, index]);
    setIndex(nextIndex);
  }

  function next() {
    goto(Math.min(index + 1, slides.length - 1), false);
  }

  function prev() {
    goto(Math.max(index - 1, 0), false);
  }

  function jumpBack() {
    setJumpStack((stack) => {
      const nextStack = [...stack];
      const previous = nextStack.pop();
      if (previous !== undefined) setIndex(previous);
      return nextStack;
    });
  }

  function renderDone(slide: ShowSlide) {
    setEvents((currentEvents) => [
      {
        type: "render_done",
        slide: slide.position,
        at: new Date().toLocaleTimeString(),
      },
      ...currentEvents.slice(0, 9),
    ]);
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!showFile || !current || !projectId || !showFileId) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-gray-950 text-white">
        <p>Show File not found.</p>
        <Button variant="secondary" onClick={() => navigate("/projects")}>
          Back to Projects
        </Button>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-950 text-white">
      <header className="flex items-center justify-between gap-4 border-b border-white/10 bg-black/40 px-4 py-3">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm text-gray-300 hover:bg-white/10 hover:text-white"
          >
            <ArrowLeft size={15} />
            Project
          </button>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <ScreenShare size={16} className="text-indigo-300" />
              <h1 className="truncate text-sm font-semibold">
                Show File v{showFile.version}
              </h1>
              <Badge variant={showFile.status === "ready" ? "green" : "red"}>
                {showFile.status}
              </Badge>
            </div>
            <p className="text-xs text-gray-400">
              Slide {current.position} of {slides.length} · {showFile.tts_provider}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            icon={<ChevronLeft size={14} />}
            disabled={index === 0}
            onClick={prev}
          >
            Prev
          </Button>
          <Button
            size="sm"
            variant="secondary"
            icon={<RotateCcw size={14} />}
            disabled={!jumpStack.length}
            onClick={jumpBack}
          >
            Jump Back
          </Button>
          <Button
            size="sm"
            variant="secondary"
            icon={<ChevronRight size={14} />}
            disabled={index === slides.length - 1}
            onClick={next}
          >
            Next
          </Button>
        </div>
      </header>

      <main className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[1fr_300px]">
        <section className="flex min-h-0 items-center justify-center bg-black p-4">
          <img
            key={current.slide_id}
            src={projectApi.showFileAssetUrl(projectId, showFileId, current.image_path)}
            alt={current.title || `Slide ${current.position}`}
            onLoad={() => renderDone(current)}
            className="max-h-full max-w-full object-contain shadow-2xl"
          />
        </section>

        <aside className="min-h-0 overflow-y-auto border-l border-white/10 bg-gray-900 p-4">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
            Goto
          </p>
          <div className="mb-5 flex flex-wrap gap-1.5">
            {slides.map((slide, slideIndex) => (
              <button
                key={slide.slide_id}
                type="button"
                onClick={() => goto(slideIndex)}
                className={`h-8 min-w-8 rounded-md px-2 text-sm font-medium ${
                  index === slideIndex
                    ? "bg-indigo-500 text-white"
                    : "bg-white/10 text-gray-200 hover:bg-white/20"
                }`}
              >
                {slide.position}
              </button>
            ))}
          </div>

          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
            Current Slide
          </p>
          <div className="mb-5 rounded-lg bg-white/5 p-3">
            <p className="font-semibold">{current.title || `Slide ${current.position}`}</p>
            <p className="mt-1 text-xs text-gray-400">
              {current.duration_seconds}s · {current.segments.length} segments
            </p>
          </div>

          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">
            Render Events
          </p>
          <div className="space-y-2">
            {events.length ? (
              events.map((event, eventIndex) => (
                <div
                  key={`${event.slide}-${event.at}-${eventIndex}`}
                  className="rounded-md bg-emerald-500/10 px-2 py-1 text-xs text-emerald-200"
                >
                  {event.type}: slide {event.slide} at {event.at}
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500">Waiting for first render_done.</p>
            )}
          </div>
        </aside>
      </main>
    </div>
  );
}
