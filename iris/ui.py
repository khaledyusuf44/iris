"""Gradio interface for Iris."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import json
from typing import Any, Iterable

from iris.engine import DirectionPressureResult, IrisEngine, PressureResult
from iris.errors import IrisError


RINGS = 4
RING_NAMES = {
    1: "Reality Contact",
    2: "Real Actor",
    3: "Existing Alternative",
    4: "Problem Truth",
}
DIRECTION_NAMES = ("Constraints", "Limitations", "Capabilities", "Reality Contact")


@dataclass(frozen=True)
class RingView:
    depth: int
    pressure: str
    why_it_bites: str
    alternative: str | None = None


@dataclass(frozen=True)
class CenterView:
    actor: str
    situation: str
    assumption_to_test: str
    next_step: str


@dataclass(frozen=True)
class SpiralView:
    idea: str
    rings: list[RingView]
    center: CenterView | None = None
    status: str = "ready"
    message: str = ""
    pending_depth: int | None = None
    center_pending: bool = False
    selected_depth: int | None = None
    iteration: str | None = None
    frame_title: str = "Idea frame 01"


@dataclass
class SpatialSession:
    idea: str = ""
    pressures: list[PressureResult] = field(default_factory=list)
    center: CenterView | None = None
    status: str = "ready"
    message: str = ""
    selected_depth: int | None = None
    iteration: str | None = None


def create_app():
    import gradio as gr

    with gr.Blocks(
        title="Iris",
        css=APP_CSS,
        js=APP_JS,
        analytics_enabled=False,
        fill_width=True,
    ) as demo:
        gr.HTML(
            render_interactive_canvas_html(),
            elem_id="iris-stage",
            container=False,
            padding=False,
        )
        engine_request = gr.Textbox(visible=False, elem_id="iris-engine-request")
        engine_response = gr.Textbox(visible=False, elem_id="iris-engine-response")
        engine_trigger = gr.Button(
            "Run Iris engine",
            visible=False,
            elem_id="iris-engine-trigger",
        )
        engine_trigger.click(
            handle_canvas_request,
            inputs=engine_request,
            outputs=engine_response,
            api_name="iris_canvas_engine",
            show_progress="hidden",
        )

    return demo


def handle_canvas_request(request_json: str) -> str:
    return run_canvas_engine(request_json)


def run_canvas_engine(
    request_json: str,
    *,
    engine: IrisEngine | None = None,
) -> str:
    try:
        request = json.loads(request_json)
        if not isinstance(request, dict):
            raise ValueError("Engine request must be a JSON object.")

        frame_id = str(request.get("frame_id", ""))
        idea = _required_text(request, "idea")
        depth = _required_depth(request)
        iterations = _idea_iterations(request.get("iterations", []))
        prior_cards = _pressure_cards(request.get("prior_cards", []))
        constraints = pressure_cards_to_constraints(prior_cards)
        frame_idea = build_frame_context(
            current_idea=idea,
            iterations=iterations,
            prior_cards=prior_cards,
        )
        iris = engine or IrisEngine()

        total = max(depth + 1, RINGS)
        results = iris.pressure_directions(
            frame_idea,
            constraints,
            depth,
            total,
            allow_soft_failures=True,
        )
        payload: dict[str, Any] = {
            "ok": True,
            "kind": "pressures",
            "frame_id": frame_id,
            "depth": depth,
            "cards": [
                {
                    "direction": result.direction,
                    "pressure": result.pressure,
                    "why_it_bites": result.why_it_bites,
                }
                for result in results
            ],
        }
        return json.dumps(payload)
    except (IrisError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return json.dumps({"ok": False, "message": str(exc)})


def build_frame_context(
    *,
    current_idea: str,
    iterations: list[dict[str, Any]],
    prior_cards: list[dict[str, Any]],
) -> str:
    history: list[tuple[int, str]] = []
    for index, item in enumerate(iterations, start=1):
        idea = str(item.get("idea", "")).strip()
        if not idea:
            continue
        try:
            version = int(item.get("version", index))
        except (TypeError, ValueError):
            version = index
        history.append((version, idea))

    if not history:
        history.append((1, current_idea))

    original_idea = history[0][1]
    lines = [
        "Frame continuity:",
        (
            "This is one continuous idea frame. The model must keep the root "
            "idea, every user iteration, and the prior AI pressure trail in "
            "view while pressuring the current iteration."
        ),
        "",
        "Current iteration:",
        current_idea,
        "",
        "Original idea:",
        original_idea,
        "",
        "Iteration history:",
    ]
    for version, idea in history:
        lines.append(f"- Idea v{version}: {idea}")

    pressure_trail = _pressure_trail_lines(prior_cards)
    if pressure_trail:
        lines.extend(
            [
                "",
                "Prior AI pressure trail:",
                *pressure_trail,
            ]
        )

    return "\n".join(lines)


def _pressure_trail_lines(cards: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for card in cards:
        pressure = str(card.get("pressure", "")).strip()
        why = str(card.get("why_it_bites", "")).strip()
        if not pressure and not why:
            continue
        try:
            depth = int(card.get("depth", 0))
        except (TypeError, ValueError):
            depth = 0
        depth_label = f"Depth {depth:02d}" if depth > 0 else "Prior depth"
        direction = str(card.get("direction", "AI pressure")).strip() or "AI pressure"
        if pressure and why:
            lines.append(
                f"- {depth_label} / {direction}: {pressure} Why it bites: {why}"
            )
        elif pressure:
            lines.append(f"- {depth_label} / {direction}: {pressure}")
        else:
            lines.append(f"- {depth_label} / {direction} why_it_bites: {why}")
    return lines


def pressure_cards_to_constraints(cards: list[dict[str, Any]]) -> list[str]:
    constraints: list[str] = []
    for card in cards:
        pressure = str(card.get("pressure", "")).strip()
        why = str(card.get("why_it_bites", "")).strip()
        if not pressure or not why:
            continue
        alternative = str(card.get("alternative", "")).strip() or None
        direction = str(card.get("direction", "")).strip()
        if direction:
            constraints.append(
                DirectionPressureResult(
                    direction=direction,
                    pressure=pressure,
                    why_it_bites=why,
                    raw="",
                ).as_constraint()
            )
        else:
            constraints.append(
                PressureResult(
                    pressure=pressure,
                    why_it_bites=why,
                    raw="",
                    alternative=alternative,
                ).as_constraint()
            )
    return constraints


def _required_text(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty string field: {key}")
    return value.strip()


def _required_depth(data: dict[str, Any]) -> int:
    value = data.get("depth")
    if isinstance(value, bool):
        raise ValueError("depth must be an integer")
    try:
        depth = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("depth must be an integer") from exc
    if depth < 1:
        raise ValueError("depth must be positive")
    return depth


def _pressure_cards(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("prior_cards must be a list")
    cards: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            cards.append(item)
    return cards


def _idea_iterations(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("iterations must be a list")
    iterations: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        idea = str(item.get("idea", "")).strip()
        if not idea:
            continue
        try:
            version = int(item.get("version", index))
        except (TypeError, ValueError):
            version = index
        iterations.append({"version": version, "idea": idea})
    return iterations


def render_interactive_canvas_html() -> str:
    return """
<section class="iris-board status-ready" id="iris-board">
  <header class="iris-boardbar" aria-label="Iris canvas header">
    <div class="iris-brand-block">
      <strong>IRIS</strong>
      <span>Pressure canvas</span>
    </div>
    <div class="iris-board-status" aria-label="Current canvas status">
      <span id="iris-status-pill">Canvas ready.</span>
      <span id="iris-frame-count">0 frames</span>
      <span id="iris-zoom-label">100%</span>
    </div>
    <div class="iris-board-tools" aria-label="Canvas controls">
      <button type="button" data-action="pan-left" aria-label="Pan left">&larr;</button>
      <button type="button" data-action="pan-up" aria-label="Pan up">&uarr;</button>
      <button type="button" data-action="pan-down" aria-label="Pan down">&darr;</button>
      <button type="button" data-action="pan-right" aria-label="Pan right">&rarr;</button>
      <button type="button" data-action="zoom-out" aria-label="Zoom out">-</button>
      <button type="button" data-action="zoom-reset" aria-label="Reset zoom">Reset</button>
      <button type="button" data-action="focus-active" aria-label="Focus active frame">Focus</button>
      <button type="button" data-action="zoom-in" aria-label="Zoom in">+</button>
    </div>
  </header>

  <div class="iris-canvas-viewport" id="iris-canvas-viewport" aria-label="Iris idea canvas">
    <div class="iris-canvas-grid" aria-hidden="true"></div>
    <main class="iris-canvas-v2" id="iris-world"></main>
  </div>
</section>
"""


def stream_spiral(idea: str) -> Iterable[str]:
    cleaned_idea = idea.strip()
    if not cleaned_idea:
        yield render_spiral_html(
            SpiralView(
                idea="",
                rings=[],
                status="error",
                message="Enter one raw idea first.",
            )
        )
        return

    engine = IrisEngine()
    pressures: list[PressureResult] = []
    constraints: list[str] = []
    yield render_spiral_html(
        SpiralView(
            idea=cleaned_idea,
            rings=[],
            status="running",
            message=f"{ring_name(1)} is active.",
            pending_depth=1,
        )
    )

    try:
        for depth in range(1, RINGS + 1):
            result = engine.pressure(cleaned_idea, constraints, depth, RINGS)
            pressures.append(result)
            constraints.append(result.as_constraint())
            next_depth = depth + 1 if depth < RINGS else None
            yield render_spiral_html(
                SpiralView(
                    idea=cleaned_idea,
                    rings=[
                        ring_to_view(index, item)
                        for index, item in enumerate(pressures, start=1)
                    ],
                    status="running",
                    message=(
                        f"{ring_name(depth)} locked."
                        if next_depth is None
                        else f"{ring_name(next_depth)} is next."
                    ),
                    pending_depth=next_depth,
                )
            )

        yield render_spiral_html(
            SpiralView(
                idea=cleaned_idea,
                rings=[
                    ring_to_view(index, item)
                    for index, item in enumerate(pressures, start=1)
                ],
                status="running",
                message="Center is forming.",
                center_pending=True,
            )
        )
        center = engine.distill(cleaned_idea, constraints)
    except IrisError as exc:
        yield render_spiral_html(
            SpiralView(
                idea=cleaned_idea,
                rings=[
                    ring_to_view(index, item)
                    for index, item in enumerate(pressures, start=1)
                ],
                status="error",
                message=str(exc),
                pending_depth=None,
                center_pending=False,
            )
        )
        return

    yield render_spiral_html(
        SpiralView(
            idea=cleaned_idea,
            rings=[
                ring_to_view(index, item)
                for index, item in enumerate(pressures, start=1)
            ],
            center=CenterView(
                actor=center.actor,
                situation=center.situation,
                assumption_to_test=center.assumption_to_test,
                next_step=center.next_step,
            ),
            status="complete",
            message="Center reached.",
        )
    )


def ring_to_view(depth: int, result: PressureResult) -> RingView:
    return RingView(
        depth=depth,
        pressure=result.pressure,
        why_it_bites=result.why_it_bites,
        alternative=result.alternative,
    )


def ring_name(depth: int) -> str:
    return RING_NAMES.get(depth, f"Ring {depth}")


def session_to_view(
    session: SpatialSession,
    *,
    pending_depth: int | None = None,
    center_pending: bool = False,
) -> SpiralView:
    return SpiralView(
        idea=session.idea,
        rings=[
            ring_to_view(index, item)
            for index, item in enumerate(session.pressures, start=1)
        ],
        center=session.center,
        status=session.status,
        message=session.message,
        pending_depth=pending_depth,
        center_pending=center_pending,
        selected_depth=session.selected_depth,
        iteration=session.iteration,
        frame_title="Active pressure stack",
    )


def render_spiral_html(view: SpiralView) -> str:
    depth = len(view.rings)
    status_text = escape(view.message or default_message(view))
    status_class = safe_class_token(view.status)
    depth_text = "Depth 00" if depth == 0 else f"Depth {depth:02d}"

    return f"""
<section class="iris-board status-{status_class}">
  <header class="iris-boardbar" aria-label="Iris canvas header">
    <div class="iris-brand-block">
      <strong>IRIS</strong>
      <span>Pressure canvas</span>
    </div>
    <div class="iris-board-status" aria-label="Current canvas status">
      <span>{status_text}</span>
      <span>MiniCPM local</span>
      <span>{escape(depth_text)}</span>
    </div>
  </header>

  <div class="iris-canvas-viewport">
    <main class="iris-canvas-v2" aria-label="Iris idea canvas">
      <section class="iris-frame iris-frame-primary" aria-label="Primary idea frame">
        <header class="iris-frame-header">
          <div>
            <span>Idea frame</span>
            <strong>{escape(view.frame_title)}</strong>
          </div>
          <div class="iris-frame-badges">
            <span>{escape(depth_text)}</span>
            <span>{escape(view.status.upper())}</span>
          </div>
        </header>
        <div class="iris-stack">
          {render_idea_card(view)}
          {render_connector("AI pressure")}
          {render_ai_cards(view)}
          {render_connector("Next iteration")}
          {render_iteration_card(view)}
          {render_center_card(view)}
        </div>
      </section>
    </main>
  </div>
</section>
"""


def render_idea_card(view: SpiralView) -> str:
    idea = view.idea or "Untitled idea"
    return f"""
<article class="iris-card iris-card-idea">
  <div class="iris-card-kicker">
    <span>Idea v1</span>
    <span>User card</span>
  </div>
  <p>{escape(idea)}</p>
</article>
"""


def render_ai_cards(view: SpiralView) -> str:
    cards = [
        render_ai_card(ring, selected=ring.depth == view.selected_depth)
        for ring in view.rings
    ]
    if view.pending_depth is not None:
        cards.append(render_pending_ai_card(view.pending_depth))
    if not cards:
        cards.append(
            """
<article class="iris-card iris-card-ai iris-card-empty">
  <div class="iris-card-kicker">
    <span>AI pressure</span>
    <span>Pending</span>
  </div>
  <p>Pressure cards pending.</p>
</article>
"""
        )

    return f'<div class="iris-ai-list" aria-label="AI pressure cards">{"".join(cards)}</div>'


def render_ai_card(ring: RingView, *, selected: bool = False) -> str:
    selected_class = " is-selected" if selected else ""
    alternative_html = (
        f'<small class="iris-alternative">Alternative: {escape(ring.alternative)}</small>'
        if ring.alternative
        else ""
    )
    return f"""
<article class="iris-card iris-card-ai{selected_class}">
  <div class="iris-card-kicker">
    <span>AI pressure</span>
    <span>{escape(ring_name(ring.depth))}</span>
  </div>
  <h3>{escape(ring.pressure)}</h3>
  <p>{escape(ring.why_it_bites)}</p>
  {alternative_html}
</article>
"""


def render_pending_ai_card(depth: int) -> str:
    return f"""
<article class="iris-card iris-card-ai is-pending">
  <div class="iris-card-kicker">
    <span>AI pressure</span>
    <span>{escape(ring_name(depth))}</span>
  </div>
  <h3>{escape(ring_name(depth))} forming</h3>
  <p>Waiting for the model pressure.</p>
  <i aria-hidden="true"></i>
</article>
"""


def render_iteration_card(view: SpiralView) -> str:
    iteration = view.iteration
    if iteration is None:
        iteration = "Next version of the idea lands here after the pressure cards."
    return f"""
<article class="iris-card iris-card-iteration">
  <div class="iris-card-kicker">
    <span>Idea v2</span>
    <span>Iteration card</span>
  </div>
  <p>{escape(iteration)}</p>
</article>
"""


def render_center_card(view: SpiralView) -> str:
    if view.center_pending:
        return f"""
{render_connector("Center")}
<article class="iris-card iris-card-center is-pending">
  <div class="iris-card-kicker">
    <span>Center</span>
    <span>Next step pending</span>
  </div>
  <h3>Center is forming.</h3>
  <p>The distilled action is waiting on the model.</p>
  <i aria-hidden="true"></i>
</article>
"""
    if view.center is None:
        return ""

    return f"""
{render_connector("Center")}
<article class="iris-card iris-card-center">
  <div class="iris-card-kicker">
    <span>Center</span>
    <span>Next step</span>
  </div>
  <h3>{escape(view.center.next_step)}</h3>
  <dl>
    <div><dt>Actor</dt><dd>{escape(view.center.actor)}</dd></div>
    <div><dt>Situation</dt><dd>{escape(view.center.situation)}</dd></div>
    <div><dt>Assumption</dt><dd>{escape(view.center.assumption_to_test)}</dd></div>
  </dl>
</article>
"""


def render_connector(label: str) -> str:
    return f"""
<div class="iris-connector" aria-hidden="true">
  <span>{escape(label)}</span>
</div>
"""


def default_message(view: SpiralView) -> str:
    if view.status == "complete":
        return "Center reached."
    if view.status == "running":
        return "Model pressure running."
    if view.status == "waiting":
        return "Awaiting next idea card."
    if view.status == "inspecting":
        return "Pressure card selected."
    if view.status == "error":
        return "Signal interrupted."
    return "Canvas ready."


def safe_class_token(value: str) -> str:
    token = "".join(
        character.lower() if character.isalnum() or character in {"-", "_"} else "-"
        for character in value
    ).strip("-")
    return token or "ready"


APP_JS = r"""
() => {
  const DIRECTIONS = ["Constraints", "Limitations", "Capabilities", "Reality Contact"];
  const MIN_SCALE = 0.35;
  const MAX_SCALE = 1.8;
  const FRAME_WIDTH = 820;

  const board = document.getElementById("iris-board");
  const viewport = document.getElementById("iris-canvas-viewport");
  const world = document.getElementById("iris-world");
  const statusPill = document.getElementById("iris-status-pill");
  const frameCount = document.getElementById("iris-frame-count");
  const zoomLabel = document.getElementById("iris-zoom-label");

  if (!board || !viewport || !world || board.dataset.irisReady === "true") {
    return;
  }
  board.dataset.irisReady = "true";

  const state = {
    frames: [],
    nextFrameNumber: 1,
    nextEntryNumber: 1,
    activeFrameId: null,
    pan: { x: 120, y: 92 },
    scale: 1,
    pointer: null,
    suppressClickUntil: 0,
    lastPointerCreateAt: 0,
    lastDragAt: 0,
    pendingFocusId: null,
  };

  function frameById(frameId) {
    return state.frames.find((frame) => frame.id === frameId);
  }

  function entryById(frame, entryId) {
    return frame.entries.find((entry) => entry.id === entryId);
  }

  function pressureEntries(frame) {
    return pressureSets(frame).flatMap((entry) => entry.cards);
  }

  function pressureSets(frame) {
    return frame.entries.filter((entry) => entry.type === "pressure_set");
  }

  function ideaEntries(frame) {
    return frame.entries.filter((entry) => entry.type === "idea");
  }

  function nextDepth(frame) {
    return pressureSets(frame).length + 1;
  }

  function makeEntryId() {
    const id = `entry-${state.nextEntryNumber}`;
    state.nextEntryNumber += 1;
    return id;
  }

  function createFrame(worldX, worldY) {
    const number = state.nextFrameNumber;
    state.nextFrameNumber += 1;
    const entryId = makeEntryId();
    const frame = {
      id: `frame-${number}`,
      number,
      x: Math.round(worldX - 140),
      y: Math.round(worldY - 48),
      status: "editing",
      complete: false,
      entries: [
        {
          id: entryId,
          type: "idea",
          version: 1,
          value: "",
          locked: false,
          error: "",
        },
      ],
    };
    state.frames.push(frame);
    state.activeFrameId = frame.id;
    state.pendingFocusId = entryId;
    setStatus(`Frame ${number} ready.`);
    render();
  }

  function setStatus(message) {
    statusPill.textContent = message;
  }

  function zoomAt(clientX, clientY, nextScale) {
    const rect = viewport.getBoundingClientRect();
    const scale = clamp(nextScale, MIN_SCALE, MAX_SCALE);
    const worldX = (clientX - rect.left - state.pan.x) / state.scale;
    const worldY = (clientY - rect.top - state.pan.y) / state.scale;
    state.pan.x = clientX - rect.left - worldX * scale;
    state.pan.y = clientY - rect.top - worldY * scale;
    state.scale = scale;
    renderTransform();
  }

  function panBy(deltaX, deltaY) {
    state.pan.x += deltaX;
    state.pan.y += deltaY;
    renderTransform();
  }

  function resetView() {
    state.scale = 1;
    state.pan = { x: 120, y: 92 };
    renderTransform();
  }

  function focusFrame(frameId = state.activeFrameId) {
    const frame = frameById(frameId);
    if (!frame) {
      resetView();
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const frameNode = world.querySelector(`[data-frame-id="${frame.id}"]`);
    const frameHeight = frameNode ? frameNode.offsetHeight : 420;
    const comfortableScale = clamp(
      Math.min((rect.width - 96) / FRAME_WIDTH, (rect.height - 96) / frameHeight, 1.1),
      0.42,
      1.1,
    );
    state.scale = comfortableScale;
    state.pan.x = rect.width / 2 - (frame.x + FRAME_WIDTH / 2) * state.scale;
    state.pan.y = rect.height / 2 - (frame.y + frameHeight / 2) * state.scale;
    renderTransform();
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function screenToWorld(clientX, clientY) {
    const rect = viewport.getBoundingClientRect();
    return {
      x: (clientX - rect.left - state.pan.x) / state.scale,
      y: (clientY - rect.top - state.pan.y) / state.scale,
    };
  }

  function renderTransform() {
    world.style.transform = `translate(${state.pan.x}px, ${state.pan.y}px) scale(${state.scale})`;
    viewport.style.setProperty("--iris-grid-x", `${state.pan.x}px`);
    viewport.style.setProperty("--iris-grid-y", `${state.pan.y}px`);
    viewport.style.setProperty("--iris-grid-size", `${24 * state.scale}px`);
    zoomLabel.textContent = `${Math.round(state.scale * 100)}%`;
  }

  function render() {
    world.innerHTML = state.frames.map(renderFrame).join("");
    frameCount.textContent = `${state.frames.length} ${state.frames.length === 1 ? "frame" : "frames"}`;
    renderTransform();
    if (state.pendingFocusId) {
      const focusId = state.pendingFocusId;
      state.pendingFocusId = null;
      window.requestAnimationFrame(() => {
        const target = world.querySelector(`[data-entry-id="${focusId}"] textarea`);
        if (target) {
          target.focus();
        }
      });
    }
  }

  function renderFrame(frame) {
    const depth = pressureSets(frame).length;
    const status = frame.complete ? "Complete" : frame.status === "thinking" ? "Thinking" : "Ready";
    const activeClass = frame.id === state.activeFrameId ? " is-active" : "";
    return `
      <section class="iris-frame${activeClass}" data-frame-id="${escapeAttr(frame.id)}" style="transform: translate(${frame.x}px, ${frame.y}px);">
        <header class="iris-frame-header" data-frame-drag="true" data-frame-id="${escapeAttr(frame.id)}" title="Drag frame">
          <div>
            <span>Idea frame</span>
            <strong>Frame ${frame.number}</strong>
          </div>
          <div class="iris-frame-badges">
            <span>Depth ${String(depth).padStart(2, "0")}</span>
            <span>${escapeHtml(status)}</span>
          </div>
        </header>
        <div class="iris-stack">
          ${renderStack(frame)}
        </div>
      </section>
    `;
  }

  function renderStack(frame) {
    const parts = [];
    frame.entries.forEach((entry, index) => {
      if (index > 0) {
        parts.push(renderConnector(connectorLabel(entry)));
      }
      parts.push(renderEntry(frame, entry));
    });
    return parts.join("");
  }

  function connectorLabel(entry) {
    if (entry.type === "idea") {
      return "Next iteration";
    }
    if (entry.type === "center") {
      return "Center";
    }
    return "AI pressure";
  }

  function renderEntry(frame, entry) {
    if (entry.type === "idea") {
      return renderIdeaEntry(frame, entry);
    }
    if (entry.type === "pressure_set") {
      return renderPressureSetEntry(entry);
    }
    if (entry.type === "center") {
      return renderCenterEntry(entry);
    }
    if (entry.type === "loading") {
      return renderLoadingEntry(entry);
    }
    if (entry.type === "error") {
      return renderErrorEntry(entry);
    }
    return "";
  }

  function renderIdeaEntry(frame, entry) {
    const disabled = entry.locked || frame.status === "thinking" || frame.complete;
    const error = entry.error ? `<p class="iris-entry-error">${escapeHtml(entry.error)}</p>` : "";
    const buttonDisabled = disabled ? "disabled" : "";
    const body = entry.locked
      ? `<p>${escapeHtml(entry.value)}</p>`
      : `<textarea data-frame-id="${escapeAttr(frame.id)}" data-entry-id="${escapeAttr(entry.id)}" rows="4" placeholder="Type the idea...">${escapeHtml(entry.value)}</textarea>`;
    const action = entry.locked
      ? ""
      : `<button type="button" data-action="proceed" data-frame-id="${escapeAttr(frame.id)}" data-entry-id="${escapeAttr(entry.id)}" ${buttonDisabled}>Proceed</button>`;

    return `
      <article class="iris-card iris-card-idea${entry.locked ? " is-locked" : " is-editing"}" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-card-kicker">
          <span>Idea v${entry.version}</span>
          <span>User card</span>
        </div>
        ${body}
        ${error}
        <div class="iris-card-actions">${action}</div>
      </article>
    `;
  }

  function renderPressureSetEntry(entry) {
    return `
      <div class="iris-pressure-set" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-pressure-grid">
          ${entry.cards.map((card) => renderPressureEntry(card)).join("")}
        </div>
      </div>
    `;
  }

  function renderPressureEntry(card) {
    return `
      <article class="iris-card iris-card-ai">
        <div class="iris-card-kicker">
          <span>AI pressure</span>
          <span>${escapeHtml(card.direction || "Direction")}</span>
        </div>
        <h3>${escapeHtml(card.pressure)}</h3>
        <p>${escapeHtml(card.why_it_bites)}</p>
      </article>
    `;
  }

  function renderCenterEntry(entry) {
    return `
      <article class="iris-card iris-card-center" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-card-kicker">
          <span>Center</span>
          <span>Next step</span>
        </div>
        <h3>${escapeHtml(entry.next_step)}</h3>
        <dl>
          <div><dt>Actor</dt><dd>${escapeHtml(entry.actor)}</dd></div>
          <div><dt>Situation</dt><dd>${escapeHtml(entry.situation)}</dd></div>
          <div><dt>Assumption</dt><dd>${escapeHtml(entry.assumption_to_test)}</dd></div>
        </dl>
      </article>
    `;
  }

  function renderLoadingEntry(entry) {
    return `
      <div class="iris-pressure-set is-pending" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-pressure-grid">
          ${DIRECTIONS.map((direction) => `
            <article class="iris-card iris-card-ai is-pending">
              <div class="iris-card-kicker">
                <span>AI pressure</span>
                <span>${escapeHtml(direction)}</span>
              </div>
              <h3>${escapeHtml(direction)} forming</h3>
              <p>MiniCPM is applying pressure.</p>
              <i aria-hidden="true"></i>
            </article>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderErrorEntry(entry) {
    return `
      <article class="iris-card iris-card-error" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-card-kicker">
          <span>Engine</span>
          <span>Retry needed</span>
        </div>
        <h3>Model call did not complete.</h3>
        <p>${escapeHtml(entry.message)}</p>
      </article>
    `;
  }

  function renderConnector(label) {
    return `
      <div class="iris-connector" aria-hidden="true">
        <span>${escapeHtml(label)}</span>
      </div>
    `;
  }

  function proceed(frameId, entryId) {
    const frame = frameById(frameId);
    if (!frame || frame.status === "thinking" || frame.complete) {
      return;
    }
    const entry = entryById(frame, entryId);
    if (!entry || entry.type !== "idea" || entry.locked) {
      return;
    }
    const value = entry.value.trim();
    if (!value) {
      entry.error = "Enter a concrete idea before proceeding.";
      state.pendingFocusId = entry.id;
      render();
      return;
    }

    const depth = nextDepth(frame);
    entry.value = value;
    entry.locked = true;
    entry.error = "";
    frame.status = "thinking";
    const loadingId = makeEntryId();
    frame.entries.push({
      id: loadingId,
      type: "loading",
      depth,
    });
    state.activeFrameId = frame.id;
    setStatus(`Frame ${frame.number}: MiniCPM thinking.`);
    render();

    callEngine(buildEnginePayload(frame, value, depth))
      .then((response) => applyEngineResponse(frame.id, loadingId, response))
      .catch((error) => applyEngineError(frame.id, loadingId, entry.id, error));
  }

  function buildEnginePayload(frame, idea, depth) {
    return {
      frame_id: frame.id,
      idea,
      depth,
      iterations: ideaEntries(frame)
        .filter((entry) => entry.value.trim())
        .map((entry) => ({ version: entry.version, idea: entry.value.trim() })),
      prior_cards: pressureEntries(frame).map((card) => ({
        depth: card.depth,
        direction: card.direction,
        pressure: card.pressure,
        why_it_bites: card.why_it_bites,
      })),
    };
  }

  async function callEngine(payload) {
    const endpoint = `${window.location.origin}/gradio_api/call/iris_canvas_engine`;
    const start = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: [JSON.stringify(payload)] }),
    });
    if (!start.ok) {
      throw new Error(`Gradio API returned HTTP ${start.status}`);
    }
    const startJson = await start.json();
    if (startJson.data) {
      return parseEnginePayload(startJson.data[0]);
    }
    if (!startJson.event_id) {
      throw new Error("Gradio API did not return an event id.");
    }

    const result = await fetch(`${endpoint}/${startJson.event_id}`);
    if (!result.ok) {
      throw new Error(`Gradio event returned HTTP ${result.status}`);
    }
    const eventText = await result.text();
    return parseGradioEventText(eventText);
  }

  function parseGradioEventText(text) {
    const blocks = text.split(/\n\n+/);
    let lastData = null;
    for (const block of blocks) {
      const lines = block.split(/\n/);
      let eventName = "message";
      const dataLines = [];
      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        }
        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trim());
        }
      }
      if (!dataLines.length) {
        continue;
      }
      const dataText = dataLines.join("\n");
      if (eventName === "error") {
        throw new Error(dataText || "Model call failed.");
      }
      try {
        const parsed = JSON.parse(dataText);
        if (Array.isArray(parsed)) {
          lastData = parsed[0];
        } else if (parsed && parsed.data) {
          lastData = parsed.data[0];
        }
      } catch (_error) {
        lastData = dataText;
      }
    }
    if (lastData === null) {
      throw new Error("Gradio API returned no model data.");
    }
    return parseEnginePayload(lastData);
  }

  function parseEnginePayload(payload) {
    const parsed = typeof payload === "string" ? JSON.parse(payload) : payload;
    if (!parsed || parsed.ok !== true) {
      throw new Error(parsed && parsed.message ? parsed.message : "Model call failed.");
    }
    return parsed;
  }

  function applyEngineResponse(frameId, loadingId, response) {
    const frame = frameById(frameId);
    if (!frame) {
      return;
    }
    const loadingIndex = frame.entries.findIndex((entry) => entry.id === loadingId);
    if (loadingIndex < 0) {
      return;
    }

    if (response.kind === "pressures") {
      frame.entries.splice(loadingIndex, 1, {
        id: loadingId,
        type: "pressure_set",
        depth: response.depth,
        cards: response.cards.map((card) => ({
          depth: response.depth,
          direction: card.direction,
          pressure: card.pressure,
          why_it_bites: card.why_it_bites,
        })),
      });
      const nextIdeaId = makeEntryId();
      frame.entries.push({
        id: nextIdeaId,
        type: "idea",
        version: ideaEntries(frame).length + 1,
        value: "",
        locked: false,
        error: "",
      });
      frame.status = "editing";
      state.pendingFocusId = nextIdeaId;
      setStatus(`Frame ${frame.number}: 4 pressures returned.`);
      render();
      return;
    }

    if (response.kind === "center") {
      frame.entries.splice(loadingIndex, 1, {
        id: loadingId,
        type: "center",
        depth: response.depth,
        actor: response.actor,
        situation: response.situation,
        assumption_to_test: response.assumption_to_test,
        next_step: response.next_step,
      });
      frame.status = "complete";
      frame.complete = true;
      setStatus(`Frame ${frame.number}: center reached.`);
      render();
    }
  }

  function applyEngineError(frameId, loadingId, ideaEntryId, error) {
    const frame = frameById(frameId);
    if (!frame) {
      return;
    }
    const loadingIndex = frame.entries.findIndex((entry) => entry.id === loadingId);
    if (loadingIndex >= 0) {
      frame.entries.splice(loadingIndex, 1, {
        id: loadingId,
        type: "error",
        message: error && error.message ? error.message : String(error),
      });
    }
    const ideaEntry = entryById(frame, ideaEntryId);
    if (ideaEntry && ideaEntry.type === "idea") {
      ideaEntry.locked = false;
      ideaEntry.error = "Model call failed. Edit or retry this idea.";
      state.pendingFocusId = ideaEntry.id;
    }
    frame.status = "error";
    setStatus(`Frame ${frame.number}: model call failed.`);
    render();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }

  function isFormTarget(target) {
    if (!(target instanceof Element)) {
      return false;
    }
    return Boolean(target.closest("textarea, input, button, select, a, [contenteditable='true']"));
  }

  function beginPan(event) {
    viewport.setPointerCapture(event.pointerId);
    state.pointer = {
      mode: "pan",
      id: event.pointerId,
      x: event.clientX,
      y: event.clientY,
      panX: state.pan.x,
      panY: state.pan.y,
      dragged: false,
    };
    viewport.classList.add("is-panning");
  }

  function beginFrameDrag(event, frameId) {
    const frame = frameById(frameId);
    if (!frame) {
      return;
    }
    viewport.setPointerCapture(event.pointerId);
    state.activeFrameId = frame.id;
    state.pointer = {
      mode: "frame",
      id: event.pointerId,
      frameId: frame.id,
      x: event.clientX,
      y: event.clientY,
      frameX: frame.x,
      frameY: frame.y,
      dragged: false,
    };
    viewport.classList.add("is-frame-dragging");
    render();
  }

  function finishPointer(event) {
    const pointer = state.pointer;
    if (!pointer || pointer.id !== event.pointerId) {
      return null;
    }
    state.pointer = null;
    viewport.classList.remove("is-panning", "is-frame-dragging");
    if (pointer.dragged) {
      state.lastDragAt = Date.now();
      state.suppressClickUntil = Date.now() + 300;
    }
    return pointer;
  }

  viewport.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || event.target.closest(".iris-board-tools") || isFormTarget(event.target)) {
      return;
    }
    const frameHeader = event.target.closest("[data-frame-drag='true']");
    if (frameHeader) {
      event.preventDefault();
      beginFrameDrag(event, frameHeader.dataset.frameId);
      return;
    }
    if (!event.target.closest(".iris-frame")) {
      beginPan(event);
    }
  });

  viewport.addEventListener("pointermove", (event) => {
    const pointer = state.pointer;
    if (!pointer || pointer.id !== event.pointerId) {
      return;
    }
    const dx = event.clientX - pointer.x;
    const dy = event.clientY - pointer.y;
    if (Math.hypot(dx, dy) > 4) {
      pointer.dragged = true;
    }
    if (pointer.dragged && pointer.mode === "pan") {
      state.pan.x = pointer.panX + dx;
      state.pan.y = pointer.panY + dy;
      renderTransform();
    }
    if (pointer.dragged && pointer.mode === "frame") {
      const frame = frameById(pointer.frameId);
      if (!frame) {
        return;
      }
      frame.x = Math.round(pointer.frameX + dx / state.scale);
      frame.y = Math.round(pointer.frameY + dy / state.scale);
      const frameNode = world.querySelector(`[data-frame-id="${frame.id}"]`);
      if (frameNode) {
        frameNode.style.transform = `translate(${frame.x}px, ${frame.y}px)`;
      }
    }
  });

  viewport.addEventListener("pointerup", (event) => {
    const pointer = finishPointer(event);
    if (!pointer) {
      return;
    }
    if (pointer.mode === "frame") {
      render();
      return;
    }
    if (pointer.dragged) {
      return;
    }
    if (pointer.mode === "pan" && !event.target.closest(".iris-frame")) {
      const point = screenToWorld(event.clientX, event.clientY);
      state.lastPointerCreateAt = Date.now();
      createFrame(point.x, point.y);
    }
  });

  viewport.addEventListener("pointercancel", (event) => {
    finishPointer(event);
  });

  viewport.addEventListener("click", (event) => {
    if (event.target.closest(".iris-frame") || event.target.closest(".iris-board-tools")) {
      return;
    }
    if (Date.now() < state.suppressClickUntil) {
      return;
    }
    if (Date.now() - state.lastPointerCreateAt < 250) {
      return;
    }
    if (Date.now() - state.lastDragAt < 250) {
      return;
    }
    const point = screenToWorld(event.clientX, event.clientY);
    createFrame(point.x, point.y);
  });

  viewport.addEventListener("wheel", (event) => {
    if (isFormTarget(event.target) && !(event.ctrlKey || event.metaKey)) {
      return;
    }
    event.preventDefault();
    if (event.ctrlKey || event.metaKey) {
      zoomAt(event.clientX, event.clientY, state.scale * Math.exp(-event.deltaY * 0.002));
      return;
    }
    if (event.altKey) {
      zoomAt(event.clientX, event.clientY, state.scale * Math.exp(-event.deltaY * 0.003));
      return;
    }
    panBy(-event.deltaX, -event.deltaY);
  }, { passive: false });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) {
      return;
    }
    const action = button.dataset.action;
    if (action === "proceed") {
      event.preventDefault();
      proceed(button.dataset.frameId, button.dataset.entryId);
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    if (action === "zoom-in") {
      zoomAt(centerX, centerY, state.scale * 1.14);
    }
    if (action === "zoom-out") {
      zoomAt(centerX, centerY, state.scale * 0.86);
    }
    if (action === "zoom-reset") {
      resetView();
    }
    if (action === "focus-active") {
      focusFrame();
    }
    if (action === "pan-left") {
      panBy(96, 0);
    }
    if (action === "pan-right") {
      panBy(-96, 0);
    }
    if (action === "pan-up") {
      panBy(0, 96);
    }
    if (action === "pan-down") {
      panBy(0, -96);
    }
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLTextAreaElement) || !target.dataset.frameId) {
      return;
    }
    const frame = frameById(target.dataset.frameId);
    if (!frame) {
      return;
    }
    const entry = entryById(frame, target.dataset.entryId);
    if (!entry || entry.type !== "idea") {
      return;
    }
    entry.value = target.value;
    entry.error = "";
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof HTMLTextAreaElement && (event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      proceed(target.dataset.frameId, target.dataset.entryId);
      return;
    }
    if (target instanceof HTMLTextAreaElement) {
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      zoomAt(centerX, centerY, state.scale * 1.12);
    }
    if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      zoomAt(centerX, centerY, state.scale * 0.88);
    }
    if (event.key === "0") {
      event.preventDefault();
      resetView();
    }
    if (event.key === "f" || event.key === "F") {
      event.preventDefault();
      focusFrame();
    }
  });

  render();
}
"""


APP_CSS = """
:root {
  --iris-ink: #07090d;
  --iris-canvas: #0c1117;
  --iris-frame: rgba(18, 24, 31, 0.84);
  --iris-frame-line: rgba(154, 171, 188, 0.24);
  --iris-card-light: #f4f0e8;
  --iris-card-cream: #fffaf0;
  --iris-card-dark: #111923;
  --iris-card-darker: #0d141d;
  --iris-text: #f2f6f8;
  --iris-ink-text: #17202a;
  --iris-muted: #aeb9c4;
  --iris-muted-strong: #687887;
  --iris-cyan: #66d9d7;
  --iris-lime: #b7e37b;
  --iris-amber: #e9b949;
  --iris-rose: #dc7bd2;
  --iris-danger: #ffb4ab;
  --iris-shadow: rgba(0, 0, 0, 0.36);
}

* {
  box-sizing: border-box;
  letter-spacing: 0;
}

body,
.gradio-container {
  margin: 0 !important;
  background: var(--iris-ink) !important;
  color: var(--iris-text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.gradio-container {
  width: 100vw !important;
  max-width: none !important;
  min-height: 100vh !important;
  padding: 0 !important;
}

.gradio-container > .main,
.gradio-container .contain,
.gradio-container .wrap,
.gradio-container main.fillable,
.gradio-container main.app,
.gradio-container .app,
.gradio-container .column,
#iris-stage,
#iris-stage > div {
  width: 100% !important;
  max-width: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 0 !important;
  background: transparent !important;
}

footer,
#iris-engine-request,
#iris-engine-response,
#iris-engine-trigger {
  display: none !important;
}

.iris-board {
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background: var(--iris-ink);
}

.iris-boardbar {
  position: relative;
  z-index: 10;
  min-height: 64px;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto auto;
  align-items: center;
  gap: 14px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(154, 171, 188, 0.18);
  background: rgba(8, 11, 15, 0.9);
  backdrop-filter: blur(16px);
}

.iris-brand-block {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}

.iris-brand-block strong {
  color: var(--iris-text);
  font-size: 18px;
  font-weight: 700;
  line-height: 1;
}

.iris-brand-block span,
.iris-board-status span,
.iris-frame-header span,
.iris-card-kicker,
.iris-connector span,
.iris-alternative,
.iris-card-center dt {
  font-family: "SFMono-Regular", "JetBrains Mono", Consolas, ui-monospace, monospace;
}

.iris-brand-block span {
  color: var(--iris-muted);
  font-size: 12px;
}

.iris-board-status,
.iris-board-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
}

.iris-board-status span,
.iris-board-tools button {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  border: 1px solid rgba(154, 171, 188, 0.18);
  border-radius: 8px;
  color: var(--iris-muted);
  background: rgba(18, 24, 31, 0.72);
  font-family: "SFMono-Regular", "JetBrains Mono", Consolas, ui-monospace, monospace;
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
}

.iris-board-status span:first-child {
  color: var(--iris-cyan);
  border-color: rgba(102, 217, 215, 0.32);
}

.iris-board-tools button {
  min-width: 32px;
  cursor: pointer;
}

.iris-board-tools button:hover {
  border-color: rgba(102, 217, 215, 0.46);
  color: var(--iris-cyan);
}

.iris-canvas-viewport {
  --iris-grid-size: 24px;
  --iris-grid-x: 120px;
  --iris-grid-y: 92px;
  position: relative;
  height: calc(100vh - 64px);
  overflow: hidden;
  touch-action: none;
  overscroll-behavior: none;
  user-select: none;
  cursor: grab;
  background:
    radial-gradient(circle at 20% 12%, rgba(102, 217, 215, 0.14), transparent 25%),
    radial-gradient(circle at 75% 70%, rgba(220, 123, 210, 0.12), transparent 28%),
    var(--iris-canvas);
}

.iris-canvas-viewport.is-panning,
.iris-canvas-viewport.is-frame-dragging {
  cursor: grabbing;
}

.iris-canvas-viewport::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(154, 171, 188, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(154, 171, 188, 0.045) 1px, transparent 1px),
    radial-gradient(circle, rgba(154, 171, 188, 0.22) 1px, transparent 1px);
  background-size:
    calc(var(--iris-grid-size) * 4) calc(var(--iris-grid-size) * 4),
    calc(var(--iris-grid-size) * 4) calc(var(--iris-grid-size) * 4),
    var(--iris-grid-size) var(--iris-grid-size);
  background-position:
    var(--iris-grid-x) var(--iris-grid-y),
    var(--iris-grid-x) var(--iris-grid-y),
    var(--iris-grid-x) var(--iris-grid-y);
  pointer-events: none;
}

.iris-canvas-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, transparent 0 44%, rgba(102, 217, 215, 0.08) 45%, transparent 46% 100%),
    linear-gradient(25deg, transparent 0 66%, rgba(233, 185, 73, 0.08) 67%, transparent 68% 100%);
  opacity: 0.75;
}

.iris-canvas-v2 {
  position: absolute;
  inset: 0;
  min-width: 100%;
  min-height: 100%;
  transform-origin: 0 0;
  will-change: transform;
}

.iris-frame {
  position: absolute;
  top: 0;
  left: 0;
  width: 820px;
  min-height: 220px;
  padding: 22px;
  border: 1px solid var(--iris-frame-line);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0)),
    var(--iris-frame);
  box-shadow: 0 24px 70px var(--iris-shadow);
  backdrop-filter: blur(12px);
  will-change: transform;
}

.iris-frame.is-active {
  border-color: rgba(102, 217, 215, 0.46);
  box-shadow: 0 0 0 1px rgba(102, 217, 215, 0.12), 0 24px 70px var(--iris-shadow);
}

.iris-frame-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  min-width: 0;
  margin-bottom: 18px;
  cursor: grab;
  user-select: none;
  touch-action: none;
}

.iris-frame-header:active {
  cursor: grabbing;
}

.iris-frame-header div:first-child {
  min-width: 0;
}

.iris-frame-header span {
  display: block;
  margin-bottom: 6px;
  color: var(--iris-muted);
  font-size: 11px;
  line-height: 1.2;
}

.iris-frame-header strong {
  display: block;
  max-width: 460px;
  color: var(--iris-text);
  font-size: 20px;
  font-weight: 650;
  line-height: 1.25;
}

.iris-frame-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.iris-frame-badges span {
  min-height: 25px;
  display: inline-flex;
  align-items: center;
  margin: 0;
  padding: 0 8px;
  border: 1px solid rgba(154, 171, 188, 0.18);
  border-radius: 8px;
  color: var(--iris-muted);
  background: rgba(7, 9, 13, 0.46);
  font-family: "SFMono-Regular", "JetBrains Mono", Consolas, ui-monospace, monospace;
  font-size: 10px;
  white-space: nowrap;
}

.iris-stack {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.iris-card {
  width: 100%;
  max-width: 642px;
  border-radius: 8px;
  border: 1px solid transparent;
  box-shadow: 0 18px 38px rgba(0, 0, 0, 0.22);
}

.iris-card-idea,
.iris-card-iteration {
  padding: 22px 24px;
  background: var(--iris-card-light);
  color: var(--iris-ink-text);
  border-color: rgba(255, 255, 255, 0.28);
}

.iris-card-kicker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--iris-muted-strong);
  font-size: 11px;
  line-height: 1.2;
}

.iris-card-idea .iris-card-kicker,
.iris-card-iteration .iris-card-kicker {
  color: #25313d !important;
  font-weight: 700;
}

.iris-card-idea .iris-card-kicker span,
.iris-card-iteration .iris-card-kicker span {
  padding: 2px 6px;
  border-radius: 6px;
  color: #25313d !important;
  background: rgba(23, 32, 42, 0.08);
}

.iris-card-ai .iris-card-kicker,
.iris-card-ai .iris-card-kicker span,
.iris-card-center .iris-card-kicker,
.iris-card-center .iris-card-kicker span,
.iris-card-error .iris-card-kicker,
.iris-card-error .iris-card-kicker span {
  color: #c7d0d9 !important;
}

.iris-card-kicker span:first-child {
  white-space: nowrap;
}

.iris-card-kicker span:last-child {
  text-align: right;
}

.iris-card p,
.iris-card h3,
.iris-card dl {
  margin: 0;
}

.iris-card-idea p,
.iris-card-iteration p {
  color: var(--iris-ink-text);
  font-size: 20px;
  font-weight: 600;
  line-height: 1.32;
}

.iris-card textarea {
  width: 100%;
  min-height: 116px;
  resize: vertical;
  border: 0;
  border-radius: 6px;
  outline: 1px solid rgba(23, 32, 42, 0.1);
  background: rgba(255, 255, 255, 0.54);
  color: var(--iris-ink-text);
  font: inherit;
  font-size: 18px;
  font-weight: 620;
  line-height: 1.35;
  padding: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  user-select: text;
}

.iris-card textarea:focus {
  outline-color: rgba(102, 217, 215, 0.74);
  box-shadow: 0 0 0 4px rgba(102, 217, 215, 0.14);
}

.iris-card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.iris-card-actions button {
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(23, 32, 42, 0.2);
  border-radius: 8px;
  background: #17202a;
  color: #f4f0e8;
  cursor: pointer;
  font-weight: 700;
}

.iris-card-actions button:hover {
  background: #0f161e;
}

.iris-card-actions button:disabled {
  cursor: progress;
  opacity: 0.6;
}

.iris-entry-error {
  margin-top: 12px !important;
  color: #8f1d18 !important;
  font-size: 13px !important;
}

.iris-connector {
  width: 100%;
  height: 54px;
  display: grid;
  place-items: center;
  position: relative;
  color: rgba(174, 185, 196, 0.76);
}

.iris-connector::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  background: linear-gradient(180deg, rgba(174, 185, 196, 0), rgba(174, 185, 196, 0.44), rgba(174, 185, 196, 0));
}

.iris-connector span {
  position: relative;
  z-index: 1;
  padding: 4px 8px;
  border: 1px solid rgba(154, 171, 188, 0.18);
  border-radius: 8px;
  background: rgba(13, 20, 29, 0.9);
  color: var(--iris-muted);
  font-size: 10px;
  line-height: 1;
}

.iris-ai-list {
  width: 100%;
  display: grid;
  place-items: center;
}

.iris-pressure-set {
  width: 100%;
}

.iris-pressure-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.iris-pressure-grid .iris-card {
  max-width: none;
}

.iris-card-ai {
  min-height: 180px;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(102, 217, 215, 0.08), rgba(102, 217, 215, 0)),
    var(--iris-card-dark);
  border-color: rgba(102, 217, 215, 0.22);
  color: var(--iris-text);
}

.iris-card-ai:nth-of-type(3n + 2) {
  border-color: rgba(220, 123, 210, 0.34);
  background:
    linear-gradient(180deg, rgba(220, 123, 210, 0.08), rgba(220, 123, 210, 0)),
    var(--iris-card-dark);
}

.iris-card-ai:nth-of-type(3n) {
  border-color: rgba(183, 227, 123, 0.34);
  background:
    linear-gradient(180deg, rgba(183, 227, 123, 0.08), rgba(183, 227, 123, 0)),
    var(--iris-card-dark);
}

.iris-card-ai.is-selected {
  border-color: rgba(233, 185, 73, 0.76);
  box-shadow: 0 0 0 1px rgba(233, 185, 73, 0.2), 0 20px 44px rgba(0, 0, 0, 0.28);
}

.iris-card-ai h3 {
  color: var(--iris-text);
  font-size: 17px;
  font-weight: 680;
  line-height: 1.32;
}

.iris-card-ai p {
  margin-top: 12px;
  color: var(--iris-muted);
  font-size: 14px;
  line-height: 1.45;
}

.iris-alternative {
  display: block;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(154, 171, 188, 0.16);
  color: var(--iris-lime);
  font-size: 11px;
  line-height: 1.35;
}

.iris-card-empty {
  min-height: 132px;
  border-style: dashed;
}

.iris-card-ai.is-pending,
.iris-card-center.is-pending {
  position: relative;
  overflow: hidden;
}

.iris-card-ai.is-pending i,
.iris-card-center.is-pending i {
  position: absolute;
  inset: auto 18px 18px 18px;
  height: 8px;
  border-radius: 8px;
  background: linear-gradient(90deg, rgba(102, 217, 215, 0.12), rgba(102, 217, 215, 0.48), rgba(102, 217, 215, 0.12));
  animation: iris-pulse 1.8s ease-in-out infinite;
}

.iris-card-center {
  padding: 22px 24px;
  border-color: rgba(183, 227, 123, 0.45);
  background:
    linear-gradient(180deg, rgba(183, 227, 123, 0.1), rgba(183, 227, 123, 0)),
    var(--iris-card-darker);
  color: var(--iris-text);
}

.iris-card-center h3,
.iris-card-error h3 {
  color: var(--iris-text);
  font-size: 17px;
  font-weight: 650;
  line-height: 1.36;
}

.iris-card-center dl {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.iris-card-center div {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.iris-card-center dt {
  color: var(--iris-muted);
  font-size: 11px;
}

.iris-card-center dd {
  margin: 0;
  color: var(--iris-text);
  font-size: 13px;
  line-height: 1.4;
}

.iris-card-error {
  padding: 18px;
  border-color: rgba(255, 180, 171, 0.44);
  background:
    linear-gradient(180deg, rgba(255, 180, 171, 0.09), rgba(255, 180, 171, 0)),
    #1d1216;
  color: var(--iris-text);
}

.iris-card-error p {
  margin-top: 12px;
  color: var(--iris-danger);
  font-size: 13px;
  line-height: 1.45;
}

@keyframes iris-pulse {
  0%,
  100% {
    opacity: 0.4;
    transform: translateX(-8px);
  }
  50% {
    opacity: 1;
    transform: translateX(8px);
  }
}

@media (max-width: 760px) {
  .iris-boardbar {
    min-height: 104px;
    grid-template-columns: 1fr;
    align-items: start;
    padding: 14px;
  }

  .iris-board-status,
  .iris-board-tools {
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .iris-canvas-viewport {
    height: calc(100vh - 104px);
  }

  .iris-pressure-grid {
    grid-template-columns: repeat(2, minmax(280px, 1fr));
  }
}
"""
