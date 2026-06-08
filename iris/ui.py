"""Gradio interface for Iris."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Iterable

from iris.engine import IrisEngine, PressureResult
from iris.errors import IrisError


RINGS = 4
RING_NAMES = {
    1: "Reality Contact",
    2: "Real Actor",
    3: "Existing Alternative",
    4: "Problem Truth",
}


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
        analytics_enabled=False,
    ) as demo:
        gr.HTML(
            render_spiral_html(sample_canvas_view()),
            elem_id="iris-stage",
        )

    return demo


def sample_canvas_view() -> SpiralView:
    return SpiralView(
        idea="A marketplace for renting tools between neighbors.",
        rings=[
            RingView(
                depth=1,
                pressure="What happens when a neighbor returns a borrowed tool broken?",
                why_it_bites="The trust failure appears before marketplace supply matters.",
            ),
            RingView(
                depth=2,
                pressure="Who decides whether a tool is safe enough to lend?",
                why_it_bites="The owner may carry the real risk while the renter gets the visible benefit.",
            ),
            RingView(
                depth=3,
                pressure="What do neighbors use today when a power saw is needed quickly: hardware store rentals?",
                why_it_bites="A store rental may already solve the urgent access moment.",
                alternative="hardware store rentals",
            ),
        ],
        status="ready",
        message="Canvas checkpoint ready.",
        selected_depth=2,
        iteration=(
            "Focus the next pass on one Saturday pickup between neighbors who already "
            "know each other and need a power drill before stores close."
        ),
        frame_title="Tool rental pressure stack",
    )


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
      <div class="iris-canvas-grid" aria-hidden="true"></div>
      <div class="iris-depth-thread iris-depth-thread-primary" aria-hidden="true"></div>
      <div class="iris-depth-thread iris-depth-thread-secondary" aria-hidden="true"></div>

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

      <section class="iris-frame iris-frame-secondary" aria-label="Secondary idea frame preview">
        <header class="iris-frame-header">
          <div>
            <span>Separate frame</span>
            <strong>Lecture notes stack</strong>
          </div>
          <div class="iris-frame-badges">
            <span>Depth 01</span>
          </div>
        </header>
        <div class="iris-mini-stack">
          <div></div>
          <div></div>
          <div></div>
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
    cards = [render_ai_card(ring, selected=ring.depth == view.selected_depth) for ring in view.rings]
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

    return f'<div class="iris-ai-row" aria-label="AI pressure cards">{"".join(cards)}</div>'


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

footer {
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
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 24px;
  border-bottom: 1px solid rgba(154, 171, 188, 0.18);
  background: rgba(8, 11, 15, 0.86);
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

.iris-board-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
}

.iris-board-status span {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1px solid rgba(154, 171, 188, 0.18);
  border-radius: 8px;
  color: var(--iris-muted);
  background: rgba(18, 24, 31, 0.72);
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
}

.iris-board-status span:first-child {
  color: var(--iris-cyan);
  border-color: rgba(102, 217, 215, 0.32);
}

.iris-canvas-viewport {
  height: calc(100vh - 64px);
  overflow: auto;
  background:
    radial-gradient(circle at 20% 12%, rgba(102, 217, 215, 0.14), transparent 25%),
    radial-gradient(circle at 75% 70%, rgba(220, 123, 210, 0.12), transparent 28%),
    var(--iris-canvas);
}

.iris-canvas-v2 {
  position: relative;
  width: 1580px;
  min-width: 100%;
  height: 1080px;
  overflow: hidden;
  cursor: grab;
  background-image:
    linear-gradient(rgba(154, 171, 188, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(154, 171, 188, 0.045) 1px, transparent 1px),
    radial-gradient(circle, rgba(154, 171, 188, 0.22) 1px, transparent 1px);
  background-size: 96px 96px, 96px 96px, 24px 24px;
  background-position: -1px -1px, -1px -1px, 0 0;
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

.iris-depth-thread {
  position: absolute;
  width: 1px;
  height: 720px;
  background: linear-gradient(180deg, rgba(102, 217, 215, 0), rgba(102, 217, 215, 0.44), rgba(102, 217, 215, 0));
  transform: rotate(18deg);
  pointer-events: none;
}

.iris-depth-thread-primary {
  top: 86px;
  left: 492px;
}

.iris-depth-thread-secondary {
  top: 276px;
  left: 1180px;
  opacity: 0.38;
}

.iris-frame {
  position: absolute;
  border: 1px solid var(--iris-frame-line);
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0)),
    var(--iris-frame);
  box-shadow: 0 24px 70px var(--iris-shadow);
  backdrop-filter: blur(12px);
}

.iris-frame-primary {
  top: 96px;
  left: 138px;
  width: 820px;
  min-height: 790px;
  padding: 22px;
}

.iris-frame-secondary {
  top: 274px;
  left: 1052px;
  width: 360px;
  min-height: 300px;
  padding: 18px;
  opacity: 0.78;
}

.iris-frame-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  min-width: 0;
  margin-bottom: 18px;
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
  border-radius: 8px;
  border: 1px solid transparent;
  box-shadow: 0 18px 38px rgba(0, 0, 0, 0.22);
}

.iris-card-idea,
.iris-card-iteration {
  max-width: 642px;
  padding: 22px 24px;
  background: var(--iris-card-light);
  color: var(--iris-ink-text);
  border-color: rgba(255, 255, 255, 0.28);
}

.iris-card-iteration {
  background: var(--iris-card-cream);
  border-color: rgba(233, 185, 73, 0.5);
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
.iris-card-center .iris-card-kicker span {
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

.iris-ai-row {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  align-items: stretch;
}

.iris-card-ai {
  min-height: 226px;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(102, 217, 215, 0.08), rgba(102, 217, 215, 0)),
    var(--iris-card-dark);
  border-color: rgba(102, 217, 215, 0.22);
  color: var(--iris-text);
}

.iris-card-ai:nth-child(2) {
  border-color: rgba(220, 123, 210, 0.34);
  background:
    linear-gradient(180deg, rgba(220, 123, 210, 0.08), rgba(220, 123, 210, 0)),
    var(--iris-card-dark);
}

.iris-card-ai:nth-child(3) {
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
  font-size: 15px;
  font-weight: 680;
  line-height: 1.28;
}

.iris-card-ai p {
  margin-top: 12px;
  color: var(--iris-muted);
  font-size: 13px;
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
  grid-column: 1 / -1;
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
  max-width: 642px;
  padding: 22px 24px;
  border-color: rgba(183, 227, 123, 0.45);
  background:
    linear-gradient(180deg, rgba(183, 227, 123, 0.1), rgba(183, 227, 123, 0)),
    var(--iris-card-darker);
  color: var(--iris-text);
}

.iris-card-center h3 {
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

.iris-mini-stack {
  display: grid;
  gap: 12px;
}

.iris-mini-stack div {
  height: 68px;
  border: 1px solid rgba(154, 171, 188, 0.22);
  border-radius: 8px;
  background: rgba(244, 240, 232, 0.88);
}

.iris-mini-stack div:nth-child(2) {
  margin-left: 24px;
  background: rgba(17, 25, 35, 0.92);
  border-color: rgba(102, 217, 215, 0.22);
}

.iris-mini-stack div:nth-child(3) {
  margin-left: 48px;
  background: rgba(255, 250, 240, 0.88);
  border-color: rgba(233, 185, 73, 0.42);
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
    height: auto;
    min-height: 72px;
    align-items: flex-start;
    flex-direction: column;
    padding: 14px;
  }

  .iris-board-status {
    width: 100%;
    justify-content: flex-start;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .iris-canvas-viewport {
    height: calc(100vh - 98px);
  }

  .iris-canvas-v2 {
    width: 1120px;
    height: 1040px;
  }

  .iris-frame-primary {
    top: 72px;
    left: 42px;
    width: 730px;
  }

  .iris-frame-secondary {
    top: 156px;
    left: 824px;
  }
}
"""
