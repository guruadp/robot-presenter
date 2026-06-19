# Ednex AI Presenter — Project Plan & Build Guide

**Document type:** Product + Engineering plan (PM / Scrum)
**Audience:** Founder/engineer building solo with an AI coding agent (Claude Code or Codex)
**Build target:** Laptop software first (V1, single-tenant) → product/SaaS + humanoid robot (V2)

---

## 1. Project Idea

A software "AI presenter" that takes a slide deck plus a shared product/company knowledge base, generates a verified narration script for each slide, then **delivers the presentation itself** — speaking in a human voice, advancing slides automatically, and answering audience questions live. It runs on a laptop first, and is architected so the same brain later drives a humanoid robot (Unitree G1/R1 EDU) as the physical presenter.

**One-liner:** Upload a deck, point it at your knowledge base; get a tireless presenter that pitches and handles Q&A — on screen now, on a robot later.

---

## 2. Description

A product pitch normally needs a knowledgeable human at every booth, demo, and timezone. This replaces the *repetitive* part of that job — delivering a consistent, fact-checked pitch and answering common questions — while keeping a human nearby for closing and rapport.

Two distinct apps share one or more knowledge bases:

- **Authoring app (offline):** ingest inputs → generate per-slide scripts grounded in the KB → human verifies every slide → freeze into an immutable, pre-rendered "Show File."
- **Runtime app (live):** load the Show File → speak each slide in a human voice → auto-advance → handle push-to-talk questions via retrieval → resume exactly where it left off.

The defining design choice is a **human-in-the-loop verification gate**: no script reaches an audience until a person has approved its facts. That gate, plus a strict refusal to over-promise (see Feasibility handling), is the project's protection against its one catastrophic failure mode — confidently stating something false or unvalidated to a customer.

---

## 3. Goals & Non-Goals

**Goals**
- Generate accurate, on-tone, spoken-style narration grounded in shared knowledge bases, with traceable citations.
- Let a human review and approve every slide's script fast.
- Deliver the talk hands-free in a natural human voice: speak, auto-advance, pause for questions, resume cleanly.
- Answer product questions from the KB; answer general/contextual questions via OpenAI (fenced); **refuse to speculate on unvalidated feasibility**; defer anything uncertain or binding to a human.
- Save and reuse decks, scripts, audio, and Q&A history so nothing is regenerated needlessly.
- Keep the architecture portable so V2 swaps laptop I/O for robot I/O without a rewrite.

**Non-Goals**
- The robot doing manipulation or walking around; it gestures/speaks next to a screen.
- Improvised social intelligence (reading the room, on-the-fly humour).
- Quoting binding prices, making contractual commitments, or asserting unvalidated use-case feasibility — always deferred to a human.
- Offline operation (network is assumed available).

---

## 4. Product Strategy

**This is two products, not one.** The scalable business is the **software** — "upload your deck + docs, get an AI that presents and handles Q&A." The **robot** is a premium, low-volume showcase and managed-service/hardware play (almost no customer owns a G1/R1). Don't let robot complexity gate the software. Build the software to stand alone; keep the robot as a marketing magnet and high-margin premium tier.

**A possible bigger wedge: the web-embed version.** The same KB + Q&A engine can power an always-on "AI product expert" embedded on a customer's website that answers prospect questions 24/7 — far bigger TAM, no venue/AV/robot complexity, and exactly what competitors monetize. The live in-room presenter is the *hard niche*. Seriously weigh web-embed as the wedge (or a parallel track) before committing the roadmap to live-room.

**Sequencing (don't build the SaaS layer first):**
1. **Single-tenant V1** — use it yourself, prove the core delivers.
2. **3–5 design partners** on a manually-provisioned version — validate willingness to pay and output quality for *their* pitches.
3. **Then** build the SaaS layer (tenancy, auth, billing, metering, self-serve).
4. **Robot** as a parallel premium track when an event justifies it.

**Three decisions that shape everything:** (a) wedge vertical — pick one sharp, repetitive-pitch market (trade-show/event sales, real estate, B2B SaaS demos, education, museums/kiosks); (b) pricing model (subscription + usage overage, given COGS); (c) runtime delivery (installed presenter vs venue-side web app).

**Build approach:** solo founder + AI coding agent (Claude Code / Codex). Keeps build cost low (see §10).

---

## 5. Competitive Landscape & Positioning

The on-screen interactive AI presenter is a **crowded, funded market** — this is a real blind spot to respect. HeyGen LiveAvatar, Tavus (Conversational Video Interface), D-ID (real-time streaming with RAG built in), Anam (low-latency), and Synthesia (enterprise avatars, 140+ languages) already do real-time avatars that listen and answer questions, mostly priced ~$0.10–0.20/min of streamed video.

**Implication:** "AI that talks and answers" is table stakes; do not build a me-too avatar. The uncontested ground is:
- **Physical robot embodiment** (none of them are robots).
- **The deck-driven presentation flow + verified-KB authoring workflow** (competitors do talking-head conversation, not "present my slides in order, then take questions, every fact human-approved").
- **A vertical focus** competitors are too broad to serve well.

Position around those three, or around the web-embed wedge — not head-to-head with HeyGen/Tavus on avatar quality.

---

## 6. Locked Assumptions (these shrink V1)

1. **Network is always available.** Cloud LLM/TTS/ASR are fine; no offline models required. (Caveat: still add a vendor-outage/venue-wifi fallback — see Risks.)
2. **OpenAI answers out-of-KB questions, fenced.** General/contextual → OpenAI; product facts (price/specs) → KB-only; **novel feasibility → no-speculation, defer to human**; low confidence → defer.
3. **Push-to-talk** for questions (button/handheld mic), not open-mic barge-in. Removes echo cancellation, DOA, speaker isolation in V1.
4. **Q&A only at gates** (end of slide / end of deck), not mid-sentence.
5. **No video in the deck for V1.** Media handling deferred.
6. **One narration block per slide; animation builds ignored in V1.**
7. **Slides rendered to images + shown in our own networked viewer** (no PowerPoint COM dependency).
8. **English only for V1.** (Multilingual is a high-priority V2 differentiator, not a rework.)
9. **Knowledge bases are decoupled, shared resources** — created/managed separately; a project attaches one or more. (Replaces the old "clean single-source KB per project" assumption.)
10. **Slides may contain images/charts** — a vision pass reads them at authoring time (replaces the old "slides carry text/notes only" assumption).
11. **A human is always present** to close, cover a glitch, and take handed-off feasibility/binding questions.
12. **Robot is informational only** — never commits to prices/deals/unvalidated feasibility.
13. **Robot target is an EDU model** (G1 EDU or R1 EDU) — base R1 has no SDK.

---

## 7. Architecture

### 7.1 Two-app model; KB as a shared resource

```
KNOWLEDGE BASES (shared, versioned)  ─┐
                                      ├─► AUTHORING: Ingest → Vision+Parse → Generate → Review → [SHOW FILE]
PROJECT (deck) attaches KB set ───────┘                                                              │
                                                                                                     ▼
                                              RUNTIME: Play (pre-rendered voice) → Advance → Q&A → Resume
```

The handoff from authoring to runtime is a single immutable, pre-rendered **Show File**. Knowledge bases live **outside** projects and are referenced by them.

### 7.2 Core principle

**The Orchestrator is the only component that writes runtime state.** Everything else is *command-in, event-out* over a transport-agnostic bus. This kills race conditions and makes robot integration a drop-in later (the robot SDK is just more components on the bus).

### 7.3 Runtime components

| Component | Responsibility |
|---|---|
| Show File Loader | Load/validate Show File (incl. baked audio), hold segments + slide map (read-only) |
| **Orchestrator** | Run FSM, own playback cursor + jump stack, make all transitions (the hub) |
| Slide Controller | Render slides to images, drive advance/jump in a networked viewer |
| Audio Playback | Play pre-rendered narration audio from the Show File |
| Live TTS | Stream Q&A answers in the same voice (ElevenLabs Flash v2.5), stop-at-sentence |
| Audio Monitor / PTT | Capture question audio on push-to-talk trigger |
| ASR | Transcribe question with endpointing |
| Q&A Engine | Classify + route (KB / OpenAI / defer), retrieve, ground, feasibility-guard, return answer + confidence |
| KB / Retrieval | Vector index + structured facts + limitations, scoped to the project's attached KBs (read-only at runtime) |
| Audit Log | Record every answered claim + source + confidence |

### 7.4 Data model

- **KnowledgeBase** — id, name, owner, **version/hash**, vector collection ref, structured facts table, **limitations/negative-space doc**, tags/namespaces for scoping.
- **Project** — id, name, deck_hash, created/updated, current_showfile_id.
- **ProjectKB (join)** — project_id, kb_id, **kb_version_at_generation** (version pinning).
- **Slide** — project_id, order, title, body text, notes, image path, **vision_summary**, content_hash.
- **Segment** — narration text, advance action, duration estimate, citations, status, **delivery style + prosody markup (SSML/ElevenLabs audio tags)**, **voice id**, **pre-rendered audio path**, **optional gesture cue (no-op in V1, ready for V2)**.
- **ShowFile** — id, project_id, version, frozen approved segments + baked audio + slide image refs + voice config + KB version pointers.
- **Cursor** — { slide_id, segment_index, sentence_index, pending_advance_action } + a jump stack.
- **Session** — id, project_id, started_at, ended_at.
- **QAEntry** — id, session_id, project_id, slide_id, question_text, answer_text, route, source, confidence, asked_at.
- **FAQ** — id, kb_id/project_id, question_pattern, canonical_answer, prerendered_audio_path, approved (promoted from frequent QAEntries).

### 7.5 Knowledge base design (decoupled, shared)

- **Many-to-many.** A project attaches a *set* of KBs and composes them (e.g., Company + Product-A + Pricing). Keep KBs granular rather than one blob.
- **Retrieval scoping.** Retrieval is scoped to the attached set, with chunk tags/namespaces so a big shared KB doesn't inject off-topic chunks into a deck's script or answers.
- **Versioning + stale reflag.** Each KB has a version/hash; each project pins the version it was generated against. A KB edit flags every project built on the old version as "KB changed — review facts," and re-flags affected narration for re-render. **Runtime tension to resolve:** Q&A answers from the *latest* KB (current facts) while narration is a frozen snapshot — a KB change must re-flag narration so it can't contradict live answers.
- **Structured + unstructured + negative space.** Vector store (prose), a structured facts table (price/specs pulled exactly, never generated), and an explicit **limitations / "what it does NOT do"** doc. The limitations doc is what lets the bot decline accurately instead of hallucinating (see Feasibility).
- **Access control.** KB edits have blast radius across projects → an owner per KB and an attach-vs-edit permission split.

### 7.6 Script generation grounding

Each slide's script is grounded in **slide content (the outline) + retrieved chunks from the attached KBs (the substance) + a vision pass on the slide image (charts/diagrams/screenshots) + the tone profile (the voice)**. Generation is **sequential** with a running summary for coherence (intro, transitions, close). Factual claims carry **citations**; structured facts come from the facts table, not generation. Narration is written **for the ear** (contractions, short sentences, direct address) with delivery markup/audio tags per segment.

**Vision:** feed the rendered slide image to a current OpenAI multimodal model (GPT-5 class; GPT-4.1 cheaper). Merge **extracted text (exact, reliable)** with the **vision pass (for what's only in pixels)** — don't rely on vision alone, as it struggles with small/rotated text and exact counts.

### 7.7 Q&A handling (incl. feasibility & injection defense)

- **Classify the question** first: product-fact, general/contextual, **novel feasibility**, or sensitive/binding.
- **Route:** product-fact → KB only; general → OpenAI (fenced); feasibility/sensitive/binding → constrained behavior + defer to human; low confidence → defer.
- **No-citation-no-claim** applies to feasibility too: if no documented capability supports a claim, the bot does not assert it.
- **Feasibility = no-speculation zone.** On a novel use case the bot answers only from documented capabilities, separates "what we do" from "what you asked," honestly marks the boundary, and **defers to a human as a lead-capture** ("we haven't validated that — let me have a solutions engineer confirm; can I take your details?"). It never renders a yes/no verdict on an unvalidated use case.
- **Prompt-injection defenses.** Treat KB documents and audience questions as untrusted input; the bot must ignore instructions embedded in either ("ignore your instructions and…"). Keep system instructions out of reach of retrieved/asked content; sanitize and constrain.
- **Audit log** records every answered claim + source + confidence.

### 7.8 Voice & human-touch

"Human voice" is ~20% of avoiding the robotic feel. Five layers, in impact order:
1. **Pre-render narration at packaging** with ElevenLabs v3 (max quality, no latency) — baked into the Show File. Runtime just plays audio; only Q&A uses live TTS (Flash v2.5, same voice).
2. **Write for the ear** — spoken-style text; flat written prose can't be rescued by any engine.
3. **Delivery markup / audio tags**, tuned at review. ElevenLabs v3 uses bracketed cues ([excited], [warmly], [pause], [sigh]); each tag affects ~the next 4–5 words. Strategic pauses are among the most human cues.
4. **Emotional arc by section** — warm intro, energetic reveals, calm on pricing/objections, strong close.
5. **Warmth in Q&A** — varied acknowledgments, mirror the asker's wording.

**Voice identity & consent:** prefer one consistent voice across narration and Q&A. Cloning a real person is the strongest "human touch" but note PVCs are not fully optimized for v3 (a designed expressive voice may beat a flatter clone); capture written consent for any clone. Live Q&A emotion can use ElevenLabs V3 Conversational (tags + context-aware delivery) at the cost of some latency.

### 7.9 Runtime state machine

`LOADING → READY → SPEAKING ⇄ ADVANCING → … → ENDED`, with a gated Q&A branch `LISTENING → PROCESSING → ANSWERING → RESUMING`. On a gate trigger: stop audio at sentence boundary → save cursor → freeze slide → answer → bridge + resume from sentence_index. A jump stack supports "go show another slide then come back." A Q&A time budget guarantees the deck finishes.

### 7.10 Persistence & reuse

Persist per project: original PPTX, parsed slides, slide images, approved scripts (markup + citations), **pre-rendered audio**, and KB embeddings — so reopening costs **zero** new synthesis/embedding. On reopen, if an approved Show File exists, **Present** is immediately available. On re-upload, content-hash the deck and each slide and **regenerate only changed slides** (plus KB-version check). The Q&A history accumulates across sessions for analytics and a **FAQ pre-bake loop** (promote frequent questions to reviewed, pre-rendered answers — the deck improves every run).

### 7.11 Robot seam (V2)

Two new components plus the gesture-cue field (already in the model): a **Robot Bridge** (maps speak/gesture/head-turn to ROS2/CycloneDDS via unitree_sdk2/unitree_ros2; republishes mic-array + person events) and a **Safety Supervisor** (e-stop, proximity hold, fall/balance, battery-aware sessions). Compute split: laptop = edge brain; robot = control stack + bridge; slides stay on a separate networked display the robot gestures toward. No expressive face → gaze/gesture, not lip-sync. Onboard speaker is weak → external PA.

### 7.12 Tech stack

- **Backend:** Python + FastAPI + WebSockets.
- **Frontend:** React + Vite + TypeScript + Tailwind.
- **Storage:** SQLite (metadata) + filesystem (images, audio).
- **Vector DB:** Chroma (local) for V1; managed (Qdrant/Pinecone) when multi-tenant.
- **LLM + embeddings + vision:** OpenAI (GPT-5 class for vision/generation).
- **TTS:** ElevenLabs **v3** (pre-render) + **Flash v2.5** (live Q&A, same voice); optional consented clone. Cartesia Sonic as low-latency alternative.
- **ASR:** OpenAI Whisper API (push-to-talk → record → transcribe).
- **State machine:** hand-rolled or `transitions`.
- **Robot (V2):** unitree_sdk2_python / unitree_ros2 over CycloneDDS, ROS2 Humble.
- **SaaS layer (V2):** Auth (Clerk/Auth0), Billing (Stripe), object storage (S3/R2).

---

## 8. V1 Features (Laptop, single-tenant + UI)

1. Create and manage **knowledge bases** as standalone resources (ingest pdf/docx/txt/md, structured facts, limitations doc, versioning).
2. Create a **project**, **select which KB(s)** it uses, upload a PPTX, set a tone-and-voice profile.
3. Parse deck → render each slide to an image → **vision pass** to understand charts/images.
4. Generate per-slide narration grounded in slide + attached KBs + vision + tone, sequentially, written for the ear, with delivery markup/audio tags, citations, and duration estimates.
5. Slide-by-slide review UI: approve / edit / regenerate-with-feedback / tone override / voice + delivery preview; stale-flagging on upstream-slide or KB change.
6. Pre-package gate (all approved, duration, citation coverage) → **pre-render narration audio** → freeze immutable Show File.
7. Networked slide viewer with programmatic advance/jump.
8. Hands-free playback of pre-rendered human-quality narration → auto-advance.
9. Push-to-talk Q&A at gates: capture → transcribe → classify/route (KB / OpenAI / defer) → confidence gate → **feasibility no-speculation** → answer → resume.
10. Audit log of every answered claim + source + confidence.
11. **Project Library & reuse** — save decks/scripts/audio/Q&A history; reopen and present without regeneration; regenerate only changed slides; Q&A analytics.
12. Presenter control panel: start/pause/stop, live state, manual advance, Q&A indicator, transcript/log, pre-flight checklist.
13. Reliability: pre-flight checks, watchdog, manual/teleprompter fallback, vendor-outage fallback, kiosk lockdown.
14. **Evals harness** — measure hallucination, factual accuracy vs KB, tone adherence, and feasibility over-claim rate before shipping.

---

## 9. V2 Features (Product/SaaS + Multilingual + Robot)

1. **Multi-tenancy** — orgs, users, roles, strict data isolation; KBs and projects scoped per org.
2. **Billing & usage metering** — plans/quotas, meter LLM/TTS/ASR, overage pricing.
3. **Self-serve onboarding** — signup, empty states, templates/sample deck, guided first run.
4. **Security & compliance** — KB encryption/isolation, voice-cloning consent capture, content moderation, ToS/privacy, GDPR retention, SOC2 path.
5. **Multilingual + accessibility** — multi-language generation/voice (one voice across languages), on-screen captions.
6. **Robot integration** — transport abstraction, Robot Bridge, embodiment (gesture track + head-turn to speaker), robot audio (mic-array, optional barge-in), Safety Supervisor, field readiness.
7. **(Optional track) Web-embed** — same engine as an always-on website "AI product expert."

---

## 10. Cost & Pricing

**Unit economics (per ~20-slide deck ≈ 18,000 chars ≈ ~18 min audio):** ElevenLabs bills ~1,000 chars/min; overage ~$0.30/1k (Creator) down to $0.12/1k (Business).
- Pre-rendered narration (one-time): **~$3–5/deck** — the dominant cost.
- Script generation + vision (OpenAI): **~$0.50–1.50/deck**.
- Per live presentation (reused deck): narration is free on replay; only Q&A (~15 questions) ≈ **$1.50–3/session**.
- One deck presented 10× ≈ **~$25 total COGS**. Reuse + pre-render amortization is what makes margins work; without reuse every show re-renders (~$5).

**Build (creating):** solo + AI agent → agent subscription (~$20–200/mo) + dev API spend (~$50–200/mo) + your time (2–4 months to V1). Cash to MVP ≈ **$1–3k** + time.

**Deploy (fixed infra, early):** hosting + DB + vector + storage + monitoring ≈ **$100–300/mo**, scaling with usage.

**SaaS layer:** Auth (~$25–100+/mo), Stripe (~2.9%+30¢/txn), later SOC2 (~$15–40k) + legal (~$2–5k).

**Robot (capex, premium tier only):** R1 EDU (~$6k+) or G1 EDU (~$40k+), plus PA, edge laptop, transport, insurance, maintenance.

**Pricing rule:** TTS scales linearly with audio minutes — everything else is small. Price as subscription **with an audio/generation quota + overage**, mirroring how ElevenLabs bills you, so COGS can never outrun revenue. Meter usage; cap free tiers hard.

---

## 11. Key Risks & Open Gaps

- **Demand not validated.** Does anyone need a deck *presented by an AI to a live audience* (vs presenting themselves)? Do customer discovery in one vertical before building more. Highest risk.
- **Crowded on-screen market** (HeyGen/Tavus/D-ID/Synthesia). Differentiate via robot + verified-deck workflow + vertical, or pivot to web-embed.
- **Hallucination / over-promising feasibility.** Mitigated by the no-speculation feasibility design, no-citation-no-claim, documented limitations, defer-to-human, and an eval over-claim metric — but reduced, not eliminated. Human present is the backstop.
- **Prompt injection (live)** via malicious KB docs or audience questions. Treat all such input as untrusted.
- **Quality measurement.** Without the evals harness you can't know if scripts/answers are good — a hard requirement.
- **Vendor concentration.** Entire COGS rides on OpenAI + ElevenLabs (price/outage/ToS risk). "Assume network" also hand-waves venue wifi — add fallbacks.
- **Legal/IP/consent.** Ownership of generated script/audio; customer-uploaded copyrighted media; voice-cloning consent at scale; wrong-fact disclaimers; ToS/privacy.
- **Cold-start onboarding, venue AV reality, support bandwidth** (solo founder can't do eng + sales + support past a few customers).

---

## 12. Epics & User Stories

> `As a <role>, I want <capability>, so that <benefit>` + acceptance criteria (AC). IDs are stable references for build prompts.

### EPIC 0 — Project Setup & Infrastructure
- **S0.1** Monorepo scaffold (FastAPI backend + Vite/React/TS frontend, shared config, env, CI, smoke tests).
- **S0.2** Config + secret management (env-loaded, explicit missing-key errors).
- **S0.3** Test harness + CI (pytest + vitest, one passing test each).

### EPIC 1 — Knowledge Base Management (standalone, shared)
- **S1.1** As a user, I want to create/manage KBs independent of projects, so that one KB serves many decks.
  - AC: KB CRUD; each KB has id, name, owner, version/hash.
- **S1.2** As a user, I want to ingest pdf/docx/txt/md into a KB, so that it's searchable.
  - AC: text extracted, chunked, embedded into a per-KB Chroma collection with source metadata + tags.
- **S1.3** As a user, I want a structured-facts table per KB, so that price/specs come from a source of truth.
  - AC: facts as structured rows with source; queryable by key.
- **S1.4** As a user, I want a limitations / "does NOT do" doc per KB, so that the bot can decline accurately.
  - AC: negative-space entries stored and retrievable by the Q&A engine.
- **S1.5** As a user, I want KB versioning, so that changes are tracked and downstream projects can be reflagged.
  - AC: every edit bumps version/hash; change events emitted.
- **S1.6** As an admin, I want KB ownership + attach-vs-edit permissions, so that edits with blast radius are controlled.
  - AC: owner per KB; edit restricted; attach allowed broadly.
- **S1.7** As the system, I want retrieval scoped to a set of KBs with tag filtering, so that big KBs don't inject noise.
  - AC: `retrieve(text, kb_set, filters) → chunks+sources+scores`.

### EPIC 2 — Project & Input Ingestion
- **S2.1** As a user, I want to create a project and **select which KB(s)** it uses, so that the deck is grounded correctly.
  - AC: project ↔ KB many-to-many join with version pinning at generation.
- **S2.2** As a user, I want to upload a PPTX parsed into ordered slides, so that the deck can be scripted.
  - AC: python-pptx → Slide records (title, body, notes); clear errors for non-PPTX.
- **S2.3** As a user, I want each slide rendered to an image, so that the viewer can display it and vision can read it.
  - AC: LibreOffice-headless (or pptx→pdf→png) per-slide image stored + linked.
- **S2.4** As a user, I want a tone-and-voice profile per project, so that narration matches our brand.
  - AC: structured profile (formality, pace, persona, do/don't, language, voice id).

### EPIC 3 — Slide Vision Understanding
- **S3.1** As the system, I want a vision pass on each slide image, so that charts/diagrams/screenshots inform the script.
  - AC: rendered image → vision model (GPT-5 class) → `vision_summary` stored per slide.
- **S3.2** As the system, I want vision merged with extracted text, so that exact data stays exact.
  - AC: extracted text used for precise figures; vision used for pixel-only meaning; merged context passed to generation.

### EPIC 4 — Script Generation
- **S4.1** Per-slide narration from slide + attached KBs + vision + tone + running summary; duration estimate; citations for factual claims; structured facts pulled exactly.
- **S4.2** Sequential generation + coherence pass (intro/transitions/close), energy varied by section.
- **S4.3** Write-for-the-ear output + delivery style + prosody markup / audio tags per segment.
- **S4.4** `regenerate(slide, feedback)` (free-text + toggles) preserving approved neighbors.

### EPIC 5 — Authoring / Review UI
- **S5.1** Slide-by-slide view (image + draft + clickable citations + duration + status badge).
- **S5.2** Approve / edit-inline (revertible versions) / regenerate-with-feedback / tone override.
- **S5.3** Voice + delivery preview per segment (select voice, tune emphasis/pauses, re-render-preview).
- **S5.4** Stale-flagging on upstream-slide edits **and on KB-version change** (no auto-overwrite of approved work).

### EPIC 6 — Packaging / Show File
- **S6.1** Pre-package gate: all approved + duration + every factual claim cited.
- **S6.2** On pass: **pre-render each segment's narration (ElevenLabs v3)** with its voice + markup, bake audio into an immutable Show File (slide refs + segments + audio + voice config + KB version pointers).
- **S6.3** Loader validates the bundle (including audio presence).

### EPIC 7 — Slide Rendering & Control
- **S7.1** Fullscreen networked viewer loading Show File images; `goto/next/prev`; `render_done` events.
- **S7.2** Advance/jump commands supporting the cursor stack.

### EPIC 8 — Speech / Human Voice
- **S8.1** Runtime playback of pre-rendered narration audio; `tts_complete` + sentence index; stop-at-sentence.
- **S8.2** Live Q&A TTS via ElevenLabs Flash v2.5 in the same voice id; stop-at-sentence.
- **S8.3** Audio output behind an interface (LaptopSpeaker now; RobotSpeaker/PA later); TTS provider swappable.

### EPIC 9 — Q&A Pipeline (with feasibility + injection defense)
- **S9.1** Push-to-talk capture → Whisper transcription with endpointing; empty capture handled gracefully.
- **S9.2** Classify question (product-fact / general / feasibility / sensitive-binding) and route accordingly.
- **S9.3** KB-grounded answers with confidence gate; **no-citation-no-claim**; product facts never from OpenAI.
- **S9.4** **Feasibility guard:** novel use cases get documented-capability-only answers + honest boundary + defer-to-human lead-capture; never a yes/no verdict.
- **S9.5** **Prompt-injection defense:** treat KB docs and questions as untrusted; ignore embedded instructions.
- **S9.6** Append every answered claim + source + confidence to an audit log.

### EPIC 10 — Orchestrator & State Machine
- **S10.1** Single-writer Orchestrator, single-threaded event loop, FSM per §7.9.
- **S10.2** Typed command/event contracts over a transport-agnostic in-process bus.
- **S10.3** Gate-based Q&A with cursor save/resume + jump stack.
- **S10.4** Q&A time budget with a "let's move on" fallback.

### EPIC 11 — Presenter Control Panel UI
- **S11.1** Real-time state (WebSocket), start/pause/stop, manual advance/prev.
- **S11.2** Q&A indicator + live transcript + last-answer + confidence + source.
- **S11.3** Pre-flight checklist (Show File, images, audio device, network/API) red/green.

### EPIC 12 — Project Library & Reuse
- **S12.1** Library home listing saved projects; reopen → if approved Show File exists, **Present** is immediately available.
- **S12.2** On re-upload, content-hash deck + slides; **regenerate only changed slides**; KB-version check.
- **S12.3** Persist Q&A history (Session + QAEntry) across sessions; analytics view (most-asked, deferrals).
- **S12.4** FAQ pre-bake loop: promote frequent questions to reviewed, pre-rendered answers.

### EPIC 13 — Evals & Quality
- **S13.1** Eval harness measuring hallucination rate, factual accuracy vs KB, tone adherence, answer correctness.
- **S13.2** **Feasibility over-claim metric** on an out-of-scope test set; gate releases on it.
- **S13.3** Regression suite run on generation/Q&A changes.

### EPIC 14 — Reliability & Ops
- **S14.1** Watchdog for a stalled deck (re-issue advance or alert).
- **S14.2** Manual/teleprompter fallback (one click to human-driven).
- **S14.3** Vendor-outage/degraded-network fallback for TTS/LLM/ASR.
- **S14.4** Kiosk lockdown + structured per-session logging.

### EPIC 15 — Packaging, Testing, Shipping (V1 done)
- **S15.1** End-to-end dry-run mode (upload → generate → review → package → play → simulated questions).
- **S15.2** Happy-path e2e test + setup/operator docs + tagged v1.0.

---

### V2 EPICS (Product/SaaS + Multilingual + Robot)

### EPIC 16 — Multi-tenancy & Accounts
- Orgs, users, roles; strict per-tenant data isolation; KBs/projects scoped to org.

### EPIC 17 — Billing & Usage Metering
- Stripe plans/quotas; meter LLM/TTS/ASR per tenant; overage billing; usage dashboard.

### EPIC 18 — Self-Serve Onboarding
- Signup, empty states, templates/sample deck, guided first-run to first "wow".

### EPIC 19 — Security & Compliance
- KB encryption/isolation; voice-cloning consent capture; content moderation on uploads/outputs; ToS/privacy; GDPR retention; SOC2 path.

### EPIC 20 — Multilingual & Accessibility
- Multi-language generation + voice (one identity across languages); on-screen captions of spoken narration/answers.

### EPIC 21 — Transport Abstraction & Robot Bridge
- Bus over ROS2/CycloneDDS with V1 tests still passing; Robot Bridge mapping speak/gesture/head-turn to unitree_sdk2/unitree_ros2; republish robot events; mock robot for tests.

### EPIC 22 — Embodiment
- Per-segment gesture cue from a gesture library; head-turn toward speaker via mic-array DOA + vision.

### EPIC 23 — Robot Audio
- Mic-array capture through the bridge (PTT default); optional barge-in upgrade behind a flag; external PA output.

### EPIC 24 — Safety Supervisor
- E-stop + proximity hold overriding the Orchestrator; fall/balance response; battery-aware sessions with graceful "wrapping up".

### EPIC 25 — Robot Integration Testing & Field Readiness
- Robot dry-run + integration suite (speak + gesture + head-turn + gated Q&A + safety) on the EDU robot; field setup docs; tagged v2.0.

---

## 13. Roadmap / Sequencing

- **Milestone 0 — Validate (before more code):** customer discovery in one vertical; decide live-room vs web-embed; kill-criteria.
- **Milestone A — KB + Authoring (Sprints 1–3):** EPIC 0 → 1 → 2 → 3 → 4 → 5 → 6. Output: select KBs, generate, verify, freeze a pre-rendered Show File.
- **Milestone B — Runtime on laptop (Sprints 4–6):** EPIC 7 → 8 → 9 → 10 → 11. Output: hands-free human-voice presentation with feasibility-safe Q&A.
- **Milestone C — Reuse + Quality + Ship V1 (Sprint 7):** EPIC 12 → 13 → 14 → 15.
- **Milestone D — Design partners:** 3–5 real customers, manual provisioning, validate value.
- **Milestone E — SaaS layer (Sprints 8–10):** EPIC 16 → 17 → 18 → 19 → 20.
- **Milestone F — Robot (Sprints 11–14):** EPIC 21 → 22 → 23 → 24 → 25.

Work top-to-bottom; commit per story; keep the dry-run/e2e + evals green before moving on.

---

## 14. Build Prompts for Claude Code / Codex

> Run in order. Each assumes prior prompts' output exists. Start each session by pasting §7 (architecture) so the agent has context. Force the agent to **plan → implement → test → summarize** per story. Feed one prompt at a time; run the test before moving on.

**Global system instruction (paste every session):**
> You are building "Ednex AI Presenter." Stack: Python/FastAPI + WebSockets backend; React/Vite/TS/Tailwind frontend; SQLite + filesystem; Chroma vector DB; OpenAI for LLM/embeddings/vision; ElevenLabs for TTS; Whisper for ASR. Core rule: the Orchestrator is the only component that writes runtime state; everything else is command-in/event-out over a transport-agnostic bus. Knowledge bases are standalone, versioned, shared resources; projects attach a set of KBs with version pinning. Data model: KnowledgeBase, Project, ProjectKB(join), Slide, Segment (with delivery markup/audio tags, voice id, pre-rendered audio path, gesture cue=null), ShowFile, Cursor+jump stack, Session, QAEntry, FAQ. Never let OpenAI answer product facts or render feasibility verdicts on unvalidated use cases. Work in small steps: plan, implement, add a test, then stop and summarize. Don't hardcode secrets. Don't add video, animations, multilingual, multi-tenancy, or robot code unless the prompt says so.

1. **Scaffold (EPIC 0)** — monorepo, health route, env config, CI, smoke tests.
2. **Data model & storage (EPIC 0/1/2)** — SQLite models for KnowledgeBase, Project, ProjectKB join (with kb_version_at_generation), Slide, Segment (incl. delivery markup/audio tags, voice id, pre-rendered audio path, gesture_cue=null), ShowFile, Cursor, Session, QAEntry, FAQ. Storage layout for images/audio. CRUD + tests.
3. **KB management (EPIC 1)** — standalone KB CRUD; ingest pdf/docx/txt/md (chunk + embed to per-KB Chroma with tags); structured-facts table; limitations/negative-space doc; versioning/hash with change events; owner + attach-vs-edit permissions; `retrieve(text, kb_set, filters)` scoped to attached KBs. Tests for scoping and versioning.
4. **Project + ingestion (EPIC 2)** — create project, attach KB set (version-pinned), upload/parse PPTX into ordered slides, render each slide to PNG, tone-and-voice profile. Tests with a sample deck.
5. **Vision pass (EPIC 3)** — send each slide image to a current OpenAI multimodal model for a `vision_summary`; merge with extracted text (exact figures from text, pixel-only meaning from vision). Tests with a stubbed vision client.
6. **Script generation (EPIC 4)** — per-slide generation from slide + attached KBs + vision + tone + running summary; write for the ear; emit delivery style + audio tags per segment; citations; structured facts pulled exactly; sequential + coherence pass with energy variation; `regenerate(slide, feedback)` preserving approved neighbors. Stubbed OpenAI client.
7. **Review UI (EPIC 5)** — slide-by-slide review (image, draft, clickable citations, duration, status); approve/edit(revertible)/regenerate/tone-override; voice + delivery preview with re-render; stale-flag on upstream-slide and KB-version change without overwriting approvals. Tests for state transitions.
8. **Packaging / Show File (EPIC 6)** — pre-package gate (approved + duration + citation coverage); on pass, **pre-render each segment's narration with ElevenLabs v3** (voice + markup) and bake into an immutable Show File (refs + segments + audio + voice config + KB version pointers); validating loader. Faked TTS render in tests.
9. **Slide viewer + control (EPIC 7)** — fullscreen networked viewer (goto/next/prev, render_done) as a standalone addressable page. Tests for command handling.
10. **Speech / human voice (EPIC 8)** — runtime playback of baked narration audio (tts_complete + sentence index, stop-at-sentence); live Q&A TTS via ElevenLabs Flash v2.5 in the same voice; audio output + TTS provider behind interfaces. Fake backends in tests.
11. **Q&A pipeline (EPIC 9)** — PTT capture → Whisper (+endpointing, empty handled); classify (product-fact/general/feasibility/sensitive); route (KB-only for facts, OpenAI fenced for general, defer for feasibility/sensitive/low-confidence); no-citation-no-claim; **feasibility guard** (documented-capability-only + boundary + defer-to-human lead-capture, never a verdict); **prompt-injection defense** (treat KB docs + questions as untrusted, ignore embedded instructions); audit log. Tests per route + feasibility + injection.
12. **Orchestrator & FSM (EPIC 10)** — single-writer Orchestrator, single-threaded loop, FSM per §7.9, cursor + jump stack, typed command/event contracts on a transport-agnostic in-process bus, gate-based Q&A save/resume, Q&A time budget. Tests for playback, gated question, resume, jump-stack.
13. **Presenter control panel (EPIC 11)** — real-time state (WebSocket), start/pause/stop, manual advance, Q&A indicator + transcript + last-answer/confidence/source, pre-flight checklist. Tests for state sync.
14. **Project library & reuse (EPIC 12)** — library home; reopen → Present if Show File exists; re-upload diff (content-hash deck + slides, regenerate only changed, KB-version check); persist Session + QAEntry; analytics view; FAQ pre-bake loop. Tests for diff + history.
15. **Evals & quality (EPIC 13)** — eval harness for hallucination, factual accuracy vs KB, tone adherence, answer correctness, and a **feasibility over-claim metric** on an out-of-scope set; regression suite; release gate. Tests for the harness itself.
16. **Reliability & ops (EPIC 14)** — watchdog, manual/teleprompter fallback, vendor-outage/degraded-network fallback, kiosk guidance, structured logging. Tests for watchdog + fallback.
17. **E2E + ship V1 (EPIC 15)** — dry-run mode (full flow + simulated questions), happy-path e2e test, setup/operator docs, tag v1.0.

**V2 prompts (after design partners validate):**
18. **Multi-tenancy (EPIC 16)** — orgs/users/roles, per-tenant isolation, KBs/projects scoped to org; existing tests still pass.
19. **Billing & metering (EPIC 17)** — Stripe plans/quotas, meter LLM/TTS/ASR per tenant, overage, usage dashboard.
20. **Onboarding (EPIC 18)** — signup, empty states, templates/sample deck, guided first run.
21. **Security & compliance (EPIC 19)** — KB encryption/isolation, voice-cloning consent capture, content moderation, ToS/privacy, retention.
22. **Multilingual & accessibility (EPIC 20)** — multi-language generation + voice (one identity), on-screen captions.
23. **Transport + Robot Bridge (EPIC 21)** — bus over ROS2/CycloneDDS with V1 tests passing; Robot Bridge mapping speak/gesture/head-turn to unitree_sdk2/unitree_ros2; republish robot events; mock robot for tests.
24. **Embodiment (EPIC 22)** — gesture cue per segment from a library; head-turn toward speaker via DOA + vision. Mock robot.
25. **Robot audio + Safety Supervisor (EPIC 23/24)** — mic-array capture (PTT default, barge-in flag); Safety Supervisor (e-stop, proximity, fall/balance, battery-aware) overriding the Orchestrator. Mock-robot tests.
26. **Robot field readiness (EPIC 25)** — robot dry-run + integration suite; field setup docs; tag v2.0.

---

## 15. Working Tips for the Coding Agent

- Commit per story; keep the dry-run/e2e + evals green before moving on.
- Re-paste §7 at the top of each session — the agent has no memory across sessions.
- Force **plan → implement → test → summarize**; reject big-bang implementations.
- Secrets in env, never inlined.
- Stop the agent on scope creep (video, animations, multilingual, multi-tenancy, robot code) until its milestone.
- Guard hardest against the three silent failures: **mistranscribed questions**, **stale KB facts**, and **over-promised feasibility**. They lie to the customer without anyone noticing — confidence-gate, KB-version reflagging, the feasibility guard, and the evals metrics exist to catch them.
