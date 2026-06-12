"""Gradio interface for Iris."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
import json
from typing import Any, Iterable

from iris.engine import (
    DirectionPressureResult,
    FinalBrief,
    IrisEngine,
    PressureResult,
)
from iris.errors import IrisError


RINGS = 4
RING_NAMES = {
    1: "Reality Contact",
    2: "Real Actor",
    3: "Existing Alternative",
    4: "Problem Truth",
}
DIRECTION_NAMES = ("Constraints", "Limitations", "Capabilities", "Reality Contact")
# Cap how many prior pressure lines we replay so a small model can still attend
# to the freshest rings instead of drowning in a long trail.
MAX_TRAIL_LINES = 10


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

    theme = gr.themes.Default(
        font=("Georgia", "Times New Roman", "serif"),
        font_mono=("ui-monospace", "SFMono-Regular", "Menlo", "monospace"),
    )

    with gr.Blocks(
        title="Iris",
        theme=theme,
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
        mode = str(request.get("mode", "pressures"))
        iterations = _idea_iterations(request.get("iterations", []))
        prior_cards = _pressure_cards(request.get("prior_cards", []))
        constraints = pressure_cards_to_constraints(prior_cards)
        conversation = build_frame_conversation(iterations, prior_cards)
        iris = engine or IrisEngine()

        if mode == "finalize":
            return _finalize_payload(
                iris,
                frame_id=frame_id,
                current_idea=idea,
                iterations=iterations,
                prior_cards=prior_cards,
                constraints=constraints,
                conversation=conversation,
            )

        depth = _required_depth(request)
        # The trail is replayed as real chat turns, so keep it out of the blob.
        frame_idea = build_frame_context(
            current_idea=idea,
            iterations=iterations,
            prior_cards=prior_cards,
            include_trail=False,
        )

        total = max(depth + 1, RINGS)
        results = iris.pressure_directions(
            frame_idea,
            constraints,
            depth,
            total,
            allow_soft_failures=True,
            conversation=conversation,
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


def _finalize_payload(
    iris: IrisEngine,
    *,
    frame_id: str,
    current_idea: str,
    iterations: list[dict[str, Any]],
    prior_cards: list[dict[str, Any]],
    constraints: list[str],
    conversation: list[dict[str, str]],
) -> str:
    frame_idea = build_frame_context(
        current_idea=current_idea,
        iterations=iterations,
        prior_cards=prior_cards,
    )
    brief: FinalBrief = iris.finalize(
        frame_idea, constraints, conversation=conversation
    )
    journey = [
        {"version": item.get("version"), "idea": item.get("idea")}
        for item in iterations
    ]
    pressures = [
        {
            "depth": card.get("depth"),
            "direction": card.get("direction"),
            "pressure": card.get("pressure"),
            "why_it_bites": card.get("why_it_bites"),
        }
        for card in prior_cards
        if str(card.get("pressure", "")).strip()
    ]
    center = brief.center
    payload: dict[str, Any] = {
        "ok": True,
        "kind": "final",
        "frame_id": frame_id,
        "refined_idea": brief.refined_idea,
        "journey": journey,
        "pressures": pressures,
        "next_step": center.next_step if center else "",
        "actor": center.actor if center else "",
        "situation": center.situation if center else "",
        "assumption_to_test": center.assumption_to_test if center else "",
    }
    return json.dumps(payload)


def build_frame_conversation(
    iterations: list[dict[str, Any]],
    prior_cards: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Replay the frame as a real chat so the model sees its own prior pressures.

    Each past idea iteration becomes a user turn, followed by an assistant turn
    listing the pressures Iris already raised at that depth. This makes the model
    treat the thread as one continuing, personalized conversation instead of a
    cold one-shot prompt.
    """

    sets: dict[int, list[dict[str, Any]]] = {}
    for card in prior_cards:
        try:
            depth = int(card.get("depth", 0))
        except (TypeError, ValueError):
            depth = 0
        sets.setdefault(depth, []).append(card)

    messages: list[dict[str, str]] = []
    for item in iterations:
        idea = str(item.get("idea", "")).strip()
        if not idea:
            continue
        try:
            version = int(item.get("version", 0))
        except (TypeError, ValueError):
            version = 0
        messages.append({"role": "user", "content": f"My idea (v{version}): {idea}"})
        lines = []
        for card in sets.get(version, []):
            pressure = str(card.get("pressure", "")).strip()
            if not pressure:
                continue
            direction = str(card.get("direction", "")).strip()
            lines.append(f"{direction}: {pressure}" if direction else pressure)
        if lines:
            messages.append(
                {
                    "role": "assistant",
                    "content": "Pressure I already raised:\n" + "\n".join(lines),
                }
            )
    return messages


def build_frame_context(
    *,
    current_idea: str,
    iterations: list[dict[str, Any]],
    prior_cards: list[dict[str, Any]],
    include_trail: bool = True,
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
    latest_version = history[-1][0]
    # Lead with the root idea so a small model anchors on it, then the live
    # iteration it must pressure now. Headings are load-bearing: the engine
    # grounding logic parses "Original idea:", "Current iteration:", and
    # "Iteration history:" sections by exact heading.
    lines = [
        "Frame continuity:",
        (
            "This is ONE continuous idea frame. Keep the original idea and every "
            "later refinement in view. Pressure the current iteration as the "
            "newest, sharpest version of the SAME original idea - build on it, "
            "never abandon the original idea, and never repeat an earlier "
            "pressure."
        ),
        "",
        "Original idea:",
        original_idea,
        "",
        "Current iteration:",
        current_idea,
        "",
        "Iteration history:",
    ]
    for version, idea in history:
        marker = " (current)" if version == latest_version else ""
        lines.append(f"- Idea v{version}: {idea}{marker}")

    # Cap the trail so the freshest pressure stays salient for a small model;
    # keep the most recent entries (deepest rings) which matter most.
    pressure_trail = _pressure_trail_lines(prior_cards) if include_trail else []
    if pressure_trail:
        trimmed = pressure_trail[-MAX_TRAIL_LINES:]
        if len(pressure_trail) > MAX_TRAIL_LINES:
            trimmed = [
                f"- (earlier pressure trimmed: {len(pressure_trail) - MAX_TRAIL_LINES} "
                "older entries)",
                *trimmed,
            ]
        lines.extend(
            [
                "",
                "Prior AI pressure trail:",
                *trimmed,
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
<section class="iris-app status-ready" id="iris-board">
  <aside class="iris-sidebar" aria-label="Iris ideas">
    <div class="iris-brand-block">
      <span class="iris-aperture-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="M12 3 L15.5 9 M21 12 L14 13 M16 20 L13 13.5 M3 12 L10 11 M8 4 L11 10.5"></path>
          <circle cx="12" cy="12" r="2.4" fill="currentColor" stroke="none"></circle>
        </svg>
      </span>
      <strong>IRIS</strong>
      <span class="iris-brand-sub">Pressure studio</span>
    </div>
    <button type="button" class="iris-new-idea" data-action="new-frame">+ New idea</button>
    <nav class="iris-frame-list" id="iris-frame-list" aria-label="Your ideas"></nav>
    <div class="iris-sidebar-foot">
      <span id="iris-frame-count">0 ideas</span>
      <span>MiniCPM local</span>
    </div>
  </aside>
  <main class="iris-main">
    <header class="iris-mainbar">
      <div class="iris-main-title">
        <span id="iris-frame-kicker">No idea selected</span>
        <strong id="iris-frame-name">Iris</strong>
      </div>
      <div class="iris-main-status">
        <span id="iris-status-pill" role="status" aria-live="polite" aria-atomic="true">Ready.</span>
        <span id="iris-depth-pill" aria-label="Ring depth"></span>
        <button type="button" id="iris-finalize-btn" class="iris-finalize-btn" data-action="finalize" disabled>Finalize &amp; export</button>
      </div>
    </header>
    <div class="iris-thread-scroll" id="iris-thread-scroll">
      <div class="iris-thread" id="iris-thread"></div>
      <div class="iris-empty-hint" id="iris-empty-hint">
        <strong>Watch an idea sharpen under pressure.</strong>
        <span>Click <b>+ New idea</b>, drop one fuzzy idea, and let Iris apply pressure.</span>
        <span>Each idea becomes a scrolling thread. Switch ideas from the left rail.</span>
      </div>
    </div>
  </main>
  <div id="iris-print-root" class="iris-print-root" aria-hidden="true"></div>
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

  const board = document.getElementById("iris-board");
  const frameList = document.getElementById("iris-frame-list");
  const thread = document.getElementById("iris-thread");
  const threadScroll = document.getElementById("iris-thread-scroll");
  const statusPill = document.getElementById("iris-status-pill");
  const depthPill = document.getElementById("iris-depth-pill");
  const frameCount = document.getElementById("iris-frame-count");
  const frameKicker = document.getElementById("iris-frame-kicker");
  const frameName = document.getElementById("iris-frame-name");
  const finalizeBtn = document.getElementById("iris-finalize-btn");

  if (!board || !thread || board.dataset.irisReady === "true") {
    return;
  }
  board.dataset.irisReady = "true";

  const state = {
    frames: [],
    nextFrameNumber: 1,
    nextEntryNumber: 1,
    activeFrameId: null,
    pendingFocusId: null,
    pendingScroll: false,
    animatedIds: new Set(),
    phaseTimer: null,
  };

  const reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const PRESSURE_PHASES = [
    "Reading your idea…",
    "Probing the soft spots…",
    "Applying pressure…",
    "Sharpening the edges…",
  ];

  function freshMark(id) {
    if (state.animatedIds.has(id)) {
      return "";
    }
    state.animatedIds.add(id);
    return " is-fresh";
  }

  function stopPhaseTimer() {
    if (state.phaseTimer) {
      clearInterval(state.phaseTimer);
      state.phaseTimer = null;
    }
  }

  function startPhaseTimer() {
    stopPhaseTimer();
    if (reduceMotion) {
      return;
    }
    let index = 0;
    state.phaseTimer = setInterval(() => {
      index = (index + 1) % PRESSURE_PHASES.length;
      const node = thread.querySelector("[data-pressure-phase]");
      if (node) {
        node.textContent = PRESSURE_PHASES[index];
      } else {
        stopPhaseTimer();
      }
    }, 3200);
  }

  function scrollBehavior() {
    return reduceMotion ? "auto" : "smooth";
  }

  function frameById(frameId) {
    return state.frames.find((frame) => frame.id === frameId);
  }

  function activeFrame() {
    return frameById(state.activeFrameId);
  }

  function entryById(frame, entryId) {
    return frame.entries.find((entry) => entry.id === entryId);
  }

  function pressureSets(frame) {
    return frame.entries.filter((entry) => entry.type === "pressure_set");
  }

  function pressureEntries(frame) {
    return pressureSets(frame).flatMap((entry) => entry.cards);
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

  function frameLabel(frame) {
    const first = ideaEntries(frame).find((entry) => entry.value.trim());
    const text = first ? first.value.trim() : "";
    if (!text) {
      return `Idea ${frame.number}`;
    }
    return text.length > 48 ? `${text.slice(0, 48).trim()}…` : text;
  }

  function setStatus(message) {
    if (statusPill) {
      statusPill.textContent = message;
    }
  }

  function createFrame() {
    const number = state.nextFrameNumber;
    state.nextFrameNumber += 1;
    const entryId = makeEntryId();
    const frame = {
      id: `frame-${number}`,
      number,
      status: "editing",
      complete: false,
      entries: [
        { id: entryId, type: "idea", version: 1, value: "", locked: false, error: "" },
      ],
    };
    state.frames.push(frame);
    state.activeFrameId = frame.id;
    state.pendingFocusId = entryId;
    state.pendingScroll = true;
    setStatus(`Idea ${number} ready.`);
    render();
  }

  function setActiveFrame(frameId) {
    if (state.activeFrameId === frameId) {
      return;
    }
    stopPhaseTimer();
    state.activeFrameId = frameId;
    render();
  }

  function render() {
    renderSidebar();
    renderThread();
    board.classList.toggle("is-empty", state.frames.length === 0);
    if (frameCount) {
      frameCount.textContent = `${state.frames.length} ${state.frames.length === 1 ? "idea" : "ideas"}`;
    }
    if (state.pendingFocusId) {
      const focusId = state.pendingFocusId;
      state.pendingFocusId = null;
      window.requestAnimationFrame(() => {
        const target = thread.querySelector(`[data-entry-id="${focusId}"] textarea`);
        if (target) {
          target.focus();
        }
      });
    }
    if (state.pendingScroll) {
      state.pendingScroll = false;
      window.requestAnimationFrame(() => {
        if (threadScroll) {
          threadScroll.scrollTo({ top: threadScroll.scrollHeight, behavior: scrollBehavior() });
        }
      });
    }
  }

  function renderSidebar() {
    frameList.innerHTML = state.frames
      .map((frame) => {
        const active = frame.id === state.activeFrameId ? " is-active" : "";
        const depth = pressureSets(frame).length;
        const badge = frame.complete ? "Done" : `D${String(depth).padStart(2, "0")}`;
        return `
          <button type="button" class="iris-frame-link${active}" data-frame-select="${escapeAttr(frame.id)}" aria-current="${frame.id === state.activeFrameId ? "page" : "false"}">
            <span class="iris-frame-link-title">${escapeHtml(frameLabel(frame))}</span>
            <span class="iris-frame-link-badge">${escapeHtml(badge)}</span>
          </button>
        `;
      })
      .join("");
  }

  function renderRingTracker(depth, complete) {
    const total = 4;
    const filled = Math.min(depth, total);
    let dots = "";
    for (let i = 0; i < total; i += 1) {
      dots += `<span class="iris-ring-dot${i < filled ? " is-on" : ""}"></span>`;
    }
    const center = `<span class="iris-ring-center${complete ? " is-on" : ""}"></span>`;
    const label = complete
      ? "Sharpened to a point"
      : depth < 1
        ? "Ring 00"
        : `Ring ${String(depth).padStart(2, "0")} · pulling toward center`;
    return `<span class="iris-ring" title="${escapeAttr(label)}" aria-label="${escapeAttr(label)}">${dots}${center}</span>`;
  }

  function renderThread() {
    const frame = activeFrame();
    if (!frame) {
      thread.innerHTML = "";
      if (frameKicker) frameKicker.textContent = "No idea selected";
      if (frameName) frameName.textContent = "Iris";
      if (depthPill) depthPill.innerHTML = renderRingTracker(0, false);
      if (finalizeBtn) finalizeBtn.disabled = true;
      return;
    }
    const depth = pressureSets(frame).length;
    if (frameKicker) frameKicker.textContent = `Idea frame ${String(frame.number).padStart(2, "0")}`;
    if (frameName) frameName.textContent = frameLabel(frame);
    if (depthPill) depthPill.innerHTML = renderRingTracker(depth, frame.complete);
    if (finalizeBtn) {
      finalizeBtn.disabled =
        depth < 1 || frame.complete || frame.status === "thinking";
      finalizeBtn.textContent = frame.complete ? "Finalized" : "Finalize & export";
    }
    if (statusPill) {
      statusPill.classList.toggle("is-thinking", frame.status === "thinking");
    }
    thread.innerHTML = renderThreadEntries(frame);
  }

  function renderThreadEntries(frame) {
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
    if (entry.type === "final") {
      return "Final version";
    }
    if (entry.type === "finalizing") {
      return "Final version";
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
    if (entry.type === "final") {
      return renderFinalEntry(frame, entry);
    }
    if (entry.type === "finalizing") {
      return renderFinalizingEntry();
    }
    if (entry.type === "error") {
      return renderErrorEntry(entry);
    }
    return "";
  }

  function renderFinalizingEntry() {
    return `
      <article class="iris-card iris-card-final is-pending">
        <div class="iris-card-kicker">
          <span>Final version</span>
          <span>Composing</span>
        </div>
        <h3>Composing the final brief…</h3>
        <p>MiniCPM is distilling everything you pressured into one sharp summary.</p>
        <i aria-hidden="true"></i>
      </article>
    `;
  }

  function renderFinalEntry(frame, entry) {
    const journey = (entry.journey || [])
      .filter((step) => step.idea)
      .map(
        (step) => `<li><span>v${escapeHtml(String(step.version))}</span> ${escapeHtml(step.idea)}</li>`,
      )
      .join("");
    const pressures = (entry.pressures || [])
      .filter((card) => card.pressure)
      .map(
        (card) =>
          `<li><span>${escapeHtml(card.direction || "Pressure")}</span> ${escapeHtml(card.pressure)}</li>`,
      )
      .join("");
    const nextStep = entry.next_step
      ? `<section class="iris-final-block"><h4>One concrete next step</h4><p>${escapeHtml(entry.next_step)}</p></section>`
      : "";
    return `
      <article class="iris-card iris-card-final${freshMark(entry.id)}" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-card-kicker">
          <span>Final version</span>
          <span>${escapeHtml(frameLabel(frame))}</span>
        </div>
        <h3>${escapeHtml(entry.refined_idea)}</h3>
        ${journey ? `<section class="iris-final-block"><h4>How the idea sharpened</h4><ol class="iris-final-journey">${journey}</ol></section>` : ""}
        ${pressures ? `<section class="iris-final-block"><h4>Pressure it faced</h4><ul class="iris-final-pressures">${pressures}</ul></section>` : ""}
        ${nextStep}
        <div class="iris-card-actions">
          <button type="button" data-action="download-pdf" data-frame-id="${escapeAttr(frame.id)}">Save PDF</button>
        </div>
      </article>
    `;
  }

  function renderIdeaEntry(frame, entry) {
    const disabled = entry.locked || frame.status === "thinking" || frame.complete;
    const error = entry.error ? `<p class="iris-entry-error">${escapeHtml(entry.error)}</p>` : "";
    const buttonDisabled = disabled ? "disabled" : "";
    const placeholder =
      entry.version === 1
        ? "e.g. an app that helps people remember names"
        : "Sharpen it — rewrite the idea after the pressure…";
    const body = entry.locked
      ? `<p>${escapeHtml(entry.value)}</p>`
      : `<textarea data-frame-id="${escapeAttr(frame.id)}" data-entry-id="${escapeAttr(entry.id)}" rows="4" aria-label="Idea version ${entry.version}" placeholder="${escapeAttr(placeholder)}">${escapeHtml(entry.value)}</textarea>`;
    const label = entry.version === 1 ? "Apply pressure" : "Sharpen again";
    const action = entry.locked
      ? ""
      : `<button type="button" data-action="proceed" data-frame-id="${escapeAttr(frame.id)}" data-entry-id="${escapeAttr(entry.id)}" ${buttonDisabled}>${label}</button>`;
    const teach =
      entry.version === 1 && !entry.locked
        ? `<p class="iris-card-teach">Drop one fuzzy idea. Iris hits it with 4 sharp questions &mdash; <b>Constraints</b>, <b>Limitations</b>, <b>Capabilities</b>, <b>Reality&nbsp;Contact</b> &mdash; then you sharpen it and go again.</p>`
        : "";
    return `
      <article class="iris-card iris-card-idea${entry.locked ? " is-locked" : " is-editing"}${freshMark(entry.id)}" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-card-kicker">
          <span>Idea v${entry.version}</span>
          <span>${entry.locked ? "Your idea" : "Your turn"}</span>
        </div>
        ${teach}
        ${body}
        ${error}
        <div class="iris-card-actions">${action}</div>
      </article>
    `;
  }

  function renderPressureSetEntry(entry) {
    const fresh = freshMark(entry.id) ? "is-fresh" : "";
    return `
      <div class="iris-pressure-set" data-entry-id="${escapeAttr(entry.id)}">
        <div class="iris-pressure-grid">
          ${entry.cards.map((card, index) => renderPressureEntry(card, index, fresh)).join("")}
        </div>
      </div>
    `;
  }

  function renderPressureEntry(card, index, fresh) {
    return `
      <article class="iris-card iris-card-ai ${fresh}" style="--i:${index}">
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
      <article class="iris-card iris-card-center${freshMark(entry.id)}" data-entry-id="${escapeAttr(entry.id)}">
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
      <div class="iris-pressure-set is-pending" data-entry-id="${escapeAttr(entry.id)}" aria-busy="true">
        <span class="sr-only">Applying pressure. This can take 15 to 25 seconds.</span>
        <div class="iris-pressure-build">
          <span class="iris-pressure-track"><span class="iris-pressure-fill"></span></span>
          <em data-pressure-phase>${escapeHtml(PRESSURE_PHASES[0])}</em>
        </div>
        <div class="iris-pressure-grid">
          ${DIRECTIONS.map((direction) => `
            <article class="iris-card iris-card-ai is-pending">
              <div class="iris-card-kicker">
                <span>AI pressure</span>
                <span>${escapeHtml(direction)}</span>
              </div>
              <h3>${escapeHtml(direction)}</h3>
              <p>Forming under pressure…</p>
              <i aria-hidden="true"></i>
            </article>
          `).join("")}
        </div>
      </div>
    `;
  }

  function renderErrorEntry(entry) {
    return `
      <article class="iris-card iris-card-error${freshMark(entry.id)}" data-entry-id="${escapeAttr(entry.id)}" role="alert">
        <div class="iris-card-kicker">
          <span>Engine</span>
          <span>Retry needed</span>
        </div>
        <h3>The local model didn't land a clean answer.</h3>
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
    frame.entries.push({ id: loadingId, type: "loading", depth });
    state.activeFrameId = frame.id;
    state.pendingScroll = true;
    setStatus(`Idea ${frame.number}: applying pressure…`);
    render();
    startPhaseTimer();

    callEngine(buildEnginePayload(frame, value, depth))
      .then((response) => applyEngineResponse(frame.id, loadingId, response))
      .catch((error) => applyEngineError(frame.id, loadingId, entry.id, error));
  }

  function finalize(frameId) {
    const frame = frameById(frameId);
    if (!frame || frame.status === "thinking" || frame.complete) {
      return;
    }
    if (pressureSets(frame).length < 1) {
      setStatus("Apply pressure at least once before finalizing.");
      return;
    }
    const lastIdea = ideaEntries(frame)
      .filter((entry) => entry.value.trim())
      .slice(-1)[0];
    const ideaText = lastIdea ? lastIdea.value.trim() : frameLabel(frame);
    frame.status = "thinking";
    const finalizingId = makeEntryId();
    frame.entries.push({ id: finalizingId, type: "finalizing" });
    state.pendingScroll = true;
    setStatus(`Idea ${frame.number}: composing final brief…`);
    render();

    const payload = {
      frame_id: frame.id,
      mode: "finalize",
      idea: ideaText,
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

    callEngine(payload)
      .then((response) => applyFinalResponse(frame.id, finalizingId, response))
      .catch((error) => applyEngineError(frame.id, finalizingId, null, error));
  }

  function applyFinalResponse(frameId, finalizingId, response) {
    stopPhaseTimer();
    const frame = frameById(frameId);
    if (!frame) {
      return;
    }
    const index = frame.entries.findIndex((entry) => entry.id === finalizingId);
    if (index < 0) {
      return;
    }
    // Drop the trailing empty idea card, if any, so the brief is the last word.
    const tail = frame.entries[frame.entries.length - 1];
    frame.entries.splice(index, 1, {
      id: finalizingId,
      type: "final",
      refined_idea: response.refined_idea || frameLabel(frame),
      journey: response.journey || [],
      pressures: response.pressures || [],
      next_step: response.next_step || "",
      actor: response.actor || "",
      situation: response.situation || "",
      assumption_to_test: response.assumption_to_test || "",
    });
    frame.entries = frame.entries.filter(
      (entry) => !(entry.type === "idea" && !entry.value.trim()),
    );
    frame.status = "complete";
    frame.complete = true;
    state.pendingScroll = true;
    setStatus(`Idea ${frame.number}: final version ready.`);
    render();
  }

  function downloadPdf(frameId) {
    const frame = frameById(frameId);
    if (!frame) {
      return;
    }
    const final = frame.entries.find((entry) => entry.type === "final");
    if (!final) {
      return;
    }
    printFallback(frame, final);
  }

  function printFallback(frame, final) {
    const printRoot = document.getElementById("iris-print-root");
    if (!printRoot) {
      return;
    }
    printRoot.innerHTML = buildPdfDoc(frame, final);
    document.body.classList.add("iris-printing");
    const cleanup = () => {
      document.body.classList.remove("iris-printing");
      printRoot.innerHTML = "";
      window.removeEventListener("afterprint", cleanup);
    };
    window.addEventListener("afterprint", cleanup);
    setStatus("Choose Save as PDF in the print dialog.");
    window.requestAnimationFrame(() => window.print());
  }

  function buildPdfDoc(frame, final) {
    const ink = "#1d1813";
    const inkSoft = "#574d41";
    const inkFaint = "#8a7f6f";
    const accent = "#aa3328";
    const rule = "#cdc3ad";
    const paper = "#f3efe4";
    const serif = "Georgia, 'Times New Roman', serif";
    const body = "Georgia, 'Times New Roman', serif";
    const mono = "ui-monospace, 'SFMono-Regular', Menlo, monospace";
    const steps = (final.journey || []).filter((step) => step.idea);
    const subtitle = steps.length
      ? `Sharpened through ${steps.length} iteration${steps.length === 1 ? "" : "s"} of pressure`
      : "Sharpened under pressure";
    const journey = steps
      .map(
        (step, index) => `
          <div style="display:grid; grid-template-columns:34px 1fr; gap:12px; padding:9px 0; border-top:1px solid ${rule};">
            <span style="font-family:${mono}; font-size:10px; letter-spacing:0.06em; color:${accent};">v${escapeHtml(String(step.version))}</span>
            <p style="margin:0; font-family:${body}; font-size:13px; line-height:1.5; color:${inkSoft};">${escapeHtml(step.idea)}${index === steps.length - 1 ? ` <span style="font-style:italic; color:${ink};">&mdash; where it landed</span>` : ""}</p>
          </div>`,
      )
      .join("");
    const pressures = (final.pressures || [])
      .filter((card) => card.pressure)
      .slice(0, 6)
      .map(
        (card, index) => `
          <div style="display:grid; grid-template-columns:34px 1fr; gap:12px; padding:9px 0; border-top:1px solid ${rule};">
            <span style="font-family:${serif}; font-size:18px; font-weight:500; line-height:1; color:${accent};">${index + 1}</span>
            <div>
              <div style="font-family:${mono}; font-size:9px; letter-spacing:0.12em; text-transform:uppercase; color:${accent}; margin-bottom:4px;">${escapeHtml(card.direction || "Pressure")}</div>
              <p style="margin:0; font-family:${serif}; font-size:14px; font-weight:500; line-height:1.4; color:${ink};">${escapeHtml(card.pressure)}</p>
            </div>
          </div>`,
      )
      .join("");
    const next = final.next_step
      ? `
        <div style="margin:30px 0 4px; padding:0 0 0 18px; border-left:3px solid ${accent};">
          <div style="font-family:${mono}; font-size:10px; letter-spacing:0.14em; text-transform:uppercase; color:${accent}; margin-bottom:9px;">The one thing to test next</div>
          <p style="margin:0; font-family:${serif}; font-size:20px; font-weight:500; font-style:italic; line-height:1.4; color:${ink};">${escapeHtml(final.next_step)}</p>
        </div>`
      : "";
    let dateLabel = "";
    try {
      dateLabel = new Date().toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch (_error) {
      dateLabel = "";
    }
    return `
      <div style="width:794px; min-height:1123px; box-sizing:border-box; display:flex; flex-direction:column; padding:66px 70px 44px; background:${paper}; color:${ink}; font-synthesis:none;">
        <div style="display:flex; align-items:flex-end; justify-content:space-between; padding-bottom:14px; border-bottom:2px solid ${ink};">
          <span style="font-family:${serif}; font-size:26px; font-weight:600; letter-spacing:0.01em; color:${ink};">Iris</span>
          <span style="font-family:${mono}; font-size:10px; letter-spacing:0.18em; text-transform:uppercase; color:${inkFaint};">Idea Brief</span>
        </div>
        <div style="font-family:${mono}; font-size:10px; letter-spacing:0.18em; text-transform:uppercase; color:${accent}; margin:34px 0 16px;">The idea, after pressure</div>
        <h1 style="margin:0; font-family:${serif}; font-size:38px; font-weight:600; line-height:1.16; letter-spacing:-0.015em; color:${ink};">${escapeHtml(final.refined_idea)}</h1>
        <p style="margin:18px 0 0; font-family:${body}; font-style:italic; font-size:14px; color:${inkSoft};">${escapeHtml(subtitle)}</p>
        ${next}
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:36px; margin-top:34px;">
          <div>
            <div style="font-family:${mono}; font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:${inkFaint}; margin-bottom:6px;">How it sharpened</div>
            ${journey || `<p style="font-family:${body}; font-size:13px; color:${inkSoft};">A single sharp idea.</p>`}
          </div>
          <div>
            <div style="font-family:${mono}; font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:${inkFaint}; margin-bottom:6px;">Pressure it survived</div>
            ${pressures || `<p style="font-family:${body}; font-size:13px; color:${inkSoft};">Pressure-tested and standing.</p>`}
          </div>
        </div>
        <div style="margin-top:auto; padding-top:22px; display:flex; justify-content:space-between; align-items:center; border-top:1px solid ${rule}; font-family:${mono}; font-size:9px; letter-spacing:0.08em; text-transform:uppercase; color:${inkFaint};">
          <span>Pressured into shape with Iris &middot; MiniCPM, run locally</span>
          <span>${escapeHtml(dateLabel)}</span>
        </div>
      </div>
    `;
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
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 90000);
    try {
      const start = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: [JSON.stringify(payload)] }),
        signal: controller.signal,
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
      const result = await fetch(`${endpoint}/${startJson.event_id}`, {
        signal: controller.signal,
      });
      if (!result.ok) {
        throw new Error(`Gradio event returned HTTP ${result.status}`);
      }
      const eventText = await result.text();
      return parseGradioEventText(eventText);
    } catch (error) {
      if (error && error.name === "AbortError") {
        throw new Error(
          "The local model took too long (over 90s). It may be overloaded — try again.",
        );
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
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
    stopPhaseTimer();
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
      state.pendingScroll = true;
      setStatus(`Idea ${frame.number}: 4 pressures returned.`);
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
      state.pendingScroll = true;
      setStatus(`Idea ${frame.number}: center reached.`);
      render();
    }
  }

  function applyEngineError(frameId, loadingId, ideaEntryId, error) {
    stopPhaseTimer();
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
    setStatus(`Idea ${frame.number}: model call failed.`);
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

  document.addEventListener("click", (event) => {
    const select = event.target.closest("[data-frame-select]");
    if (select) {
      setActiveFrame(select.dataset.frameSelect);
      return;
    }
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
    if (action === "new-frame") {
      createFrame();
      return;
    }
    if (action === "finalize") {
      event.preventDefault();
      finalize(button.dataset.frameId || state.activeFrameId);
      return;
    }
    if (action === "download-pdf") {
      event.preventDefault();
      downloadPdf(button.dataset.frameId || state.activeFrameId);
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
    const link = frameList.querySelector(`[data-frame-select="${frame.id}"] .iris-frame-link-title`);
    if (link) {
      link.textContent = frameLabel(frame);
    }
    if (frame.id === state.activeFrameId && frameName) {
      frameName.textContent = frameLabel(frame);
    }
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      target instanceof HTMLTextAreaElement &&
      (event.metaKey || event.ctrlKey) &&
      event.key === "Enter"
    ) {
      event.preventDefault();
      proceed(target.dataset.frameId, target.dataset.entryId);
    }
  });

  // Land the user straight in a focused idea, not a dead empty screen.
  if (state.frames.length === 0) {
    createFrame();
  } else {
    render();
  }
}
"""


APP_CSS = """
:root {
  --paper: #f3efe4;
  --paper-2: #ece6d8;
  --paper-3: #e4ddcb;
  --ink: #1d1813;
  --ink-soft: #574d41;
  --ink-faint: #8a7f6f;
  --rule: #cdc3ad;
  --rule-strong: #b3a78d;
  --accent: #aa3328;
  --accent-deep: #842318;

  --serif: Georgia, "Times New Roman", serif;
  --body: Georgia, "Times New Roman", serif;
  --mono: ui-monospace, "SFMono-Regular", "JetBrains Mono", Menlo, monospace;

  --ease: cubic-bezier(0.22, 1, 0.36, 1);
  --d-fast: 0.16s;
  --d-mid: 0.4s;

  --iris-sidebar-w: 290px;
}

* {
  box-sizing: border-box;
}

/* Force the light/paper theme even when the OS is in dark mode, and override
   Gradio's themed text-color variables so buttons/spans inherit ink, not white. */
html {
  color-scheme: light;
}

body,
.gradio-container {
  margin: 0 !important;
  background: var(--paper) !important;
  color: var(--ink) !important;
  font-family: var(--body) !important;
  font-synthesis: none;
}

.gradio-container {
  width: 100vw !important;
  max-width: none !important;
  min-height: 100vh !important;
  padding: 0 !important;
  --body-text-color: #1d1813 !important;
  --body-text-color-subdued: #574d41 !important;
  --button-secondary-text-color: #1d1813 !important;
  --button-secondary-text-color-hover: #1d1813 !important;
  --link-text-color: #aa3328 !important;
  --block-title-text-color: #1d1813 !important;
  --color-accent: #aa3328 !important;
}

#iris-board .iris-frame-link {
  color: var(--ink-soft);
}

#iris-board .iris-frame-link-title {
  color: inherit;
}

#iris-board .iris-frame-link.is-active,
#iris-board .iris-frame-link.is-active .iris-frame-link-title {
  color: var(--ink);
}

#iris-board .iris-frame-link-badge {
  color: var(--ink-faint);
}

#iris-board .iris-connector span {
  color: var(--ink-faint);
}

#iris-board .iris-card-center .iris-card-kicker,
#iris-board .iris-card-final .iris-card-kicker,
#iris-board .iris-card-ai .iris-card-kicker {
  color: var(--accent);
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

.sr-only {
  position: absolute !important;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ---- shell ---- */
.iris-app {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background: var(--paper);
  background-image:
    repeating-linear-gradient(0deg, transparent, transparent 27px, rgba(29, 24, 19, 0.018) 27px, rgba(29, 24, 19, 0.018) 28px);
}

/* ---- sidebar: the masthead + index ---- */
.iris-sidebar {
  width: var(--iris-sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 26px 22px;
  border-right: 1px solid var(--rule-strong);
  background: var(--paper-2);
}

.iris-brand-block {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 8px 10px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--ink);
}

.iris-aperture-mark {
  display: inline-flex;
  color: var(--ink);
}

.iris-brand-block strong {
  font-family: var(--serif);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 0.9;
  color: var(--ink);
}

.iris-brand-sub {
  grid-column: 1 / -1;
  font-family: var(--body);
  font-style: italic;
  font-size: 13px;
  color: var(--ink-soft);
}

.iris-new-idea {
  width: 100%;
  min-height: 42px;
  border: 1px solid var(--ink);
  border-radius: 0;
  background: transparent;
  color: var(--ink);
  font-family: var(--mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--d-fast), color var(--d-fast);
}

.iris-new-idea:hover {
  background: var(--ink);
  color: var(--paper);
}

.iris-frame-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.iris-frame-link {
  display: flex;
  align-items: baseline;
  gap: 10px;
  width: 100%;
  padding: 13px 4px;
  border: 0;
  border-top: 1px solid var(--rule);
  background: transparent;
  color: var(--ink-soft);
  text-align: left;
  cursor: pointer;
  transition: color var(--d-fast);
}

.iris-frame-list .iris-frame-link:last-child {
  border-bottom: 1px solid var(--rule);
}

.iris-frame-link:hover {
  color: var(--ink);
}

.iris-frame-link.is-active {
  color: var(--ink);
}

.iris-frame-link.is-active .iris-frame-link-title {
  text-decoration: underline;
  text-decoration-color: var(--accent);
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}

.iris-frame-link-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--serif);
  font-size: 15px;
  font-weight: 500;
}

.iris-frame-link-badge {
  flex-shrink: 0;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--ink-faint);
}

.iris-sidebar-foot {
  display: flex;
  justify-content: space-between;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

/* ---- main column ---- */
.iris-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.iris-mainbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 40px 16px;
  border-bottom: 1px solid var(--rule-strong);
}

.iris-main-title {
  min-width: 0;
}

.iris-main-title > span:first-child {
  display: block;
  margin-bottom: 4px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.iris-main-title strong {
  display: block;
  max-width: 60vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 600;
  color: var(--ink);
}

.iris-main-status {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

#iris-status-pill {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.04em;
  color: var(--ink-soft);
}

#iris-status-pill.is-thinking {
  color: var(--accent);
  animation: iris-blink 1.4s steps(1) infinite;
}

@keyframes iris-blink {
  50% { opacity: 0.45; }
}

.iris-ring {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.iris-ring-dot,
.iris-ring-center {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1px solid var(--rule-strong);
  transition: background var(--d-mid) var(--ease), border-color var(--d-mid);
}

.iris-ring-dot.is-on {
  background: var(--ink);
  border-color: var(--ink);
}

.iris-ring-center {
  width: 9px;
  height: 9px;
  margin-left: 3px;
  transform: rotate(45deg);
  border-radius: 0;
}

.iris-ring-center.is-on {
  background: var(--accent);
  border-color: var(--accent);
}

.iris-finalize-btn {
  min-height: 34px;
  padding: 0 16px;
  border: 1px solid var(--accent);
  border-radius: 0;
  background: transparent;
  color: var(--accent);
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--d-fast), color var(--d-fast);
}

.iris-finalize-btn:hover:not(:disabled) {
  background: var(--accent);
  color: var(--paper);
}

.iris-finalize-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ---- thread ---- */
.iris-thread-scroll {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.iris-thread {
  max-width: 680px;
  margin: 0 auto;
  padding: 44px 40px 120px;
}

.iris-empty-hint {
  position: absolute;
  top: 44%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: none;
  flex-direction: column;
  gap: 12px;
  max-width: 460px;
  text-align: center;
}

.iris-app.is-empty .iris-empty-hint {
  display: flex;
}

.iris-empty-hint strong {
  font-family: var(--serif);
  font-size: 26px;
  font-weight: 500;
  font-style: italic;
  color: var(--ink);
}

.iris-empty-hint span {
  font-size: 15px;
  line-height: 1.6;
  color: var(--ink-soft);
}

.iris-empty-hint b {
  color: var(--accent);
  font-weight: 600;
}

/* shared card reset (no boxes by default) */
.iris-card {
  width: 100%;
}

@keyframes iris-set {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

.iris-card.is-fresh,
.iris-pressure-grid .iris-card-ai.is-fresh {
  animation: iris-set var(--d-mid) var(--ease) both;
  animation-delay: calc(var(--i, 0) * 90ms);
}

.iris-card-kicker {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.iris-card p,
.iris-card h3,
.iris-card dl {
  margin: 0;
}

/* idea = the author's line, set large */
.iris-card-idea,
.iris-card-iteration {
  padding: 6px 0 4px;
  border-top: 2px solid var(--ink);
}

.iris-card-idea .iris-card-kicker span:last-child,
.iris-card-iteration .iris-card-kicker span:last-child {
  color: var(--accent);
}

.iris-card-idea p,
.iris-card-iteration p {
  font-family: var(--serif);
  font-size: 27px;
  font-weight: 500;
  line-height: 1.22;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.iris-card-teach {
  margin: 0 0 16px !important;
  font-family: var(--body) !important;
  font-style: italic;
  font-size: 14px !important;
  line-height: 1.55 !important;
  color: var(--ink-soft) !important;
}

.iris-card-teach b {
  font-style: normal;
  font-weight: 600;
  color: var(--accent);
}

.iris-card textarea {
  width: 100%;
  min-height: 96px;
  margin-top: 6px;
  resize: vertical;
  border: 1px solid var(--rule-strong);
  border-radius: 0;
  outline: none;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 400;
  line-height: 1.3;
  padding: 14px 16px;
}

.iris-card textarea::placeholder {
  color: var(--ink-faint);
  font-style: italic;
}

.iris-card textarea:focus {
  border-color: var(--ink);
}

.iris-card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.iris-card-actions button {
  min-height: 38px;
  padding: 0 22px;
  border: 1px solid var(--ink);
  border-radius: 0;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--d-fast), color var(--d-fast);
}

.iris-card-actions button:hover:not(:disabled) {
  background: transparent;
  color: var(--ink);
}

.iris-card-actions button:disabled {
  opacity: 0.4;
  cursor: default;
}

.iris-entry-error {
  margin-top: 12px !important;
  font-family: var(--mono) !important;
  font-size: 12px !important;
  color: var(--accent) !important;
}

/* connector: a printed sigil between movements */
.iris-connector {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 26px 0;
  color: var(--ink-faint);
}

.iris-connector::before,
.iris-connector::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--rule);
}

.iris-connector span {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

/* pressure: a numbered apparatus of footnotes */
.iris-pressure-set {
  width: 100%;
}

.iris-pressure-grid {
  width: 100%;
  display: flex;
  flex-direction: column;
  counter-reset: iris-note;
}

.iris-card-ai {
  display: grid;
  grid-template-columns: 30px 1fr;
  gap: 16px;
  padding: 18px 0;
  border-top: 1px solid var(--rule);
}

.iris-pressure-grid .iris-card-ai:last-child {
  border-bottom: 1px solid var(--rule);
}

.iris-card-ai::before {
  counter-increment: iris-note;
  content: counter(iris-note);
  font-family: var(--serif);
  font-size: 22px;
  font-weight: 500;
  line-height: 1;
  color: var(--accent);
}

.iris-card-ai .iris-card-kicker {
  grid-column: 2;
  margin-bottom: 6px;
  color: var(--accent);
}

.iris-card-ai .iris-card-kicker span:first-child {
  display: none;
}

.iris-card-ai h3 {
  grid-column: 2;
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 500;
  line-height: 1.32;
  color: var(--ink);
}

.iris-card-ai p {
  grid-column: 2;
  margin-top: 8px;
  font-family: var(--body);
  font-style: italic;
  font-size: 15px;
  line-height: 1.55;
  color: var(--ink-soft);
}

.iris-alternative {
  display: block;
  margin-top: 10px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent-deep);
}

/* loading: setting the questions in type */
.iris-pressure-build {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 0 14px;
  border-top: 2px solid var(--ink);
}

.iris-pressure-build em {
  flex-shrink: 0;
  font-family: var(--body);
  font-style: italic;
  font-size: 14px;
  color: var(--ink-soft);
  order: 2;
}

.iris-pressure-track {
  position: relative;
  flex: 1;
  height: 2px;
  background: var(--rule);
  order: 1;
  overflow: hidden;
}

.iris-pressure-fill {
  position: absolute;
  inset: 0 auto 0 0;
  width: 6%;
  background: var(--accent);
  animation: iris-build 18s cubic-bezier(0.2, 0.6, 0.1, 1) forwards;
}

@keyframes iris-build {
  0% { width: 4%; }
  80% { width: 86%; }
  100% { width: 93%; }
}

.iris-card-ai.is-pending h3,
.iris-card-ai.is-pending p {
  color: var(--ink-faint);
}

.iris-card-ai.is-pending i {
  grid-column: 2;
  display: block;
  height: 10px;
  width: 60%;
  margin-top: 8px;
  background: var(--rule);
  animation: iris-typeset 1.6s ease-in-out infinite;
}

.iris-pressure-set.is-pending .iris-card-ai:nth-child(2) i { animation-delay: 0.2s; width: 75%; }
.iris-pressure-set.is-pending .iris-card-ai:nth-child(3) i { animation-delay: 0.4s; width: 50%; }
.iris-pressure-set.is-pending .iris-card-ai:nth-child(4) i { animation-delay: 0.6s; width: 68%; }

@keyframes iris-typeset {
  0%, 100% { opacity: 0.45; }
  50% { opacity: 0.9; }
}

/* center + final: the point, set as a colophon */
.iris-card-center,
.iris-card-final {
  padding: 22px 0 6px;
  border-top: 3px double var(--accent);
}

.iris-card-center .iris-card-kicker,
.iris-card-final .iris-card-kicker {
  color: var(--accent);
}

.iris-card-center h3,
.iris-card-final h3 {
  font-family: var(--serif);
  font-size: 23px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--ink);
}

.iris-card-final h3 {
  font-style: italic;
}

.iris-card-center dl {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.iris-card-center div {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 14px;
  align-items: baseline;
  border-top: 1px solid var(--rule);
  padding-top: 10px;
}

.iris-card-center dt {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.iris-card-center dd {
  margin: 0;
  font-family: var(--body);
  font-size: 15px;
  line-height: 1.5;
  color: var(--ink);
}

.iris-final-block {
  margin-top: 18px;
}

.iris-final-block h4 {
  margin: 0 0 8px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.iris-final-block p {
  font-size: 15px;
  line-height: 1.55;
  color: var(--ink);
}

.iris-final-journey,
.iris-final-pressures {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.iris-final-journey li,
.iris-final-pressures li {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ink-soft);
}

.iris-final-journey li span,
.iris-final-pressures li span {
  margin-right: 8px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--accent);
}

.iris-card-error {
  padding: 18px 0 6px;
  border-top: 2px solid var(--accent);
}

.iris-card-error h3 {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 500;
  color: var(--ink);
}

.iris-card-error p {
  margin-top: 10px;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.5;
  color: var(--accent-deep);
}

/* Print-to-PDF: a typeset one-page brief on paper. */
.iris-print-root {
  display: none;
}

@page {
  margin: 0;
}

@media print {
  body.iris-printing * {
    visibility: hidden !important;
  }
  body.iris-printing .iris-print-root,
  body.iris-printing .iris-print-root * {
    visibility: visible !important;
  }
  body.iris-printing .iris-print-root {
    display: block !important;
    position: absolute;
    inset: 0;
  }
}

@media (max-width: 860px) {
  .iris-app {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }
  .iris-sidebar {
    width: 100%;
  }
  .iris-frame-list {
    max-height: 160px;
  }
  .iris-mainbar {
    flex-wrap: wrap;
    padding: 14px 18px;
    gap: 10px;
  }
  .iris-main-status {
    flex-wrap: wrap;
  }
  .iris-thread {
    padding: 28px 18px 90px;
  }
  .iris-main-title strong {
    max-width: 80vw;
  }
}
"""
