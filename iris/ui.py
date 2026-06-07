"""Gradio interface for Iris."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable

from iris.engine import IrisEngine, PressureResult
from iris.errors import IrisError
from iris.seeds import DEFAULT_IDEAS


RINGS = 4


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


def create_app():
    import gradio as gr

    with gr.Blocks(
        title="Iris",
        css=APP_CSS,
        analytics_enabled=False,
    ) as demo:
        with gr.Row(elem_classes=["iris-workbench"]):
            with gr.Column(scale=4, min_width=320, elem_classes=["iris-input-panel"]):
                gr.Markdown("# Iris")
                idea = gr.Textbox(
                    label="Idea",
                    lines=4,
                    max_lines=6,
                    placeholder="A marketplace for renting tools between neighbors.",
                    value=DEFAULT_IDEAS[0],
                    elem_classes=["iris-idea-input"],
                )
                with gr.Row(elem_classes=["iris-actions"]):
                    run = gr.Button("Run spiral", variant="primary")
                    clear = gr.Button("Clear", variant="secondary")
                with gr.Row(elem_classes=["iris-seeds"]):
                    seed_buttons = [
                        gr.Button(seed_label(index), variant="secondary")
                        for index, _seed in enumerate(DEFAULT_IDEAS, start=1)
                    ]

            with gr.Column(scale=7, min_width=460, elem_classes=["iris-stage-panel"]):
                output = gr.HTML(
                    render_spiral_html(SpiralView(idea=DEFAULT_IDEAS[0], rings=[])),
                    elem_id="iris-stage",
                )

        run.click(stream_spiral, inputs=idea, outputs=output)
        clear.click(lambda: "", outputs=idea).then(
            lambda: render_spiral_html(SpiralView(idea="", rings=[])), outputs=output
        )
        for button, seed in zip(seed_buttons, DEFAULT_IDEAS, strict=True):
            button.click(lambda selected=seed: selected, outputs=idea).then(
                lambda selected=seed: render_spiral_html(
                    SpiralView(idea=selected, rings=[])
                ),
                outputs=output,
            )

    return demo


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
            message="Opening the first ring.",
        )
    )

    try:
        for depth in range(1, RINGS + 1):
            result = engine.pressure(cleaned_idea, constraints, depth, RINGS)
            pressures.append(result)
            constraints.append(result.as_constraint())
            yield render_spiral_html(
                SpiralView(
                    idea=cleaned_idea,
                    rings=[
                        ring_to_view(index, item)
                        for index, item in enumerate(pressures, start=1)
                    ],
                    status="running",
                    message=f"Ring {depth} locked.",
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


def seed_label(index: int) -> str:
    labels = {
        1: "Medication",
        2: "Tools",
        3: "Flashcards",
    }
    return labels.get(index, f"Seed {index}")


def render_spiral_html(view: SpiralView) -> str:
    active_depth = len(view.rings)
    center_active = view.center is not None
    stage_class = f"iris-visual status-{escape(view.status)}"
    idea_text = escape(view.idea or "Awaiting idea")
    status_text = escape(view.message or default_message(view))
    rings_html = "\n".join(
        render_ring_marker(depth, active_depth, center_active)
        for depth in range(1, RINGS + 1)
    )
    ring_cards = "\n".join(render_ring_card(ring) for ring in view.rings)
    center_html = render_center(view.center)

    return f"""
<section class="{stage_class}">
  <div class="iris-visual-grid">
    <div class="iris-orbit" aria-label="Iris spiral progress">
      <div class="iris-pulse"></div>
      {rings_html}
      <div class="iris-core {'is-lit' if center_active else ''}">
        <span>{'CENTER' if center_active else 'IRIS'}</span>
      </div>
    </div>
    <div class="iris-readout">
      <p class="iris-kicker">Current idea</p>
      <h2>{idea_text}</h2>
      <p class="iris-status">{status_text}</p>
    </div>
  </div>
  <div class="iris-results">
    {ring_cards or '<div class="iris-empty">The rings are waiting.</div>'}
    {center_html}
  </div>
</section>
"""


def render_ring_marker(depth: int, active_depth: int, center_active: bool) -> str:
    state = "is-complete" if active_depth >= depth else "is-waiting"
    if not center_active and active_depth + 1 == depth:
        state = "is-next"
    return f'<div class="iris-ring iris-ring-{depth} {state}"><span>{depth}</span></div>'


def render_ring_card(ring: RingView) -> str:
    alt = (
        f'<p class="iris-alt"><span>Alternative</span>{escape(ring.alternative)}</p>'
        if ring.alternative
        else ""
    )
    return f"""
<article class="iris-ring-card">
  <div class="iris-ring-meta">Ring {ring.depth}</div>
  <h3>{escape(ring.pressure)}</h3>
  {alt}
  <p>{escape(ring.why_it_bites)}</p>
</article>
"""


def render_center(center: CenterView | None) -> str:
    if center is None:
        return ""
    return f"""
<article class="iris-center-card">
  <div class="iris-ring-meta">Center</div>
  <h3>{escape(center.next_step)}</h3>
  <dl>
    <div><dt>Actor</dt><dd>{escape(center.actor)}</dd></div>
    <div><dt>Situation</dt><dd>{escape(center.situation)}</dd></div>
    <div><dt>Assumption</dt><dd>{escape(center.assumption_to_test)}</dd></div>
  </dl>
</article>
"""


def default_message(view: SpiralView) -> str:
    if view.status == "complete":
        return "Center reached."
    if view.status == "running":
        return "Applying pressure."
    if view.status == "error":
        return "The spiral stopped."
    return "Ready."


APP_CSS = """
:root {
  --iris-bg: #08090d;
  --iris-panel: #11151d;
  --iris-panel-2: #151b24;
  --iris-line: rgba(255, 255, 255, 0.12);
  --iris-text: #f3f5f1;
  --iris-muted: #a6adbb;
  --iris-green: #9fe870;
  --iris-cyan: #6ee7f9;
  --iris-red: #ff6b6b;
  --iris-gold: #ffd166;
}

body,
.gradio-container {
  background: var(--iris-bg) !important;
  color: var(--iris-text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

.gradio-container {
  max-width: 1240px !important;
  padding: 18px !important;
}

footer {
  display: none !important;
}

.iris-workbench {
  gap: 18px;
  align-items: stretch;
}

.iris-input-panel,
.iris-stage-panel {
  background: transparent;
  border: 1px solid var(--iris-line);
  border-radius: 8px;
  padding: 18px;
}

.iris-input-panel h1 {
  margin: 0 0 14px;
  font-size: 34px;
  line-height: 1;
  letter-spacing: 0;
}

.iris-actions,
.iris-seeds {
  gap: 8px;
}

.iris-actions button,
.iris-seeds button {
  border-radius: 6px !important;
}

.iris-visual {
  min-height: 720px;
}

.iris-visual-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(280px, 1.1fr);
  gap: 18px;
  align-items: center;
}

.iris-orbit {
  position: relative;
  width: min(100%, 430px);
  aspect-ratio: 1;
  margin: 0 auto;
}

.iris-pulse,
.iris-ring,
.iris-core {
  position: absolute;
  inset: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
}

.iris-pulse {
  width: 24%;
  aspect-ratio: 1;
  background: radial-gradient(circle, rgba(159, 232, 112, 0.28), rgba(159, 232, 112, 0));
  animation: iris-pulse 2.6s ease-in-out infinite;
}

.iris-ring {
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.13);
  color: rgba(255, 255, 255, 0.36);
  transition: border-color 280ms ease, color 280ms ease, box-shadow 280ms ease;
}

.iris-ring span {
  position: absolute;
  top: 8px;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--iris-bg);
  border: 1px solid currentColor;
  font-size: 12px;
  font-weight: 700;
}

.iris-ring-1 { width: 88%; aspect-ratio: 1; }
.iris-ring-2 { width: 68%; aspect-ratio: 1; }
.iris-ring-3 { width: 48%; aspect-ratio: 1; }
.iris-ring-4 { width: 30%; aspect-ratio: 1; }

.iris-ring.is-complete {
  border-color: rgba(159, 232, 112, 0.82);
  color: var(--iris-green);
  box-shadow: 0 0 28px rgba(159, 232, 112, 0.12);
}

.iris-ring.is-next {
  border-color: rgba(110, 231, 249, 0.68);
  color: var(--iris-cyan);
  animation: iris-ring-breathe 2.2s ease-in-out infinite;
}

.iris-core {
  width: 16%;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  background: #121821;
  border: 1px solid var(--iris-line);
  color: var(--iris-muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
}

.iris-core.is-lit {
  color: #0c1117;
  background: var(--iris-green);
  box-shadow: 0 0 44px rgba(159, 232, 112, 0.42);
}

.iris-readout h2 {
  margin: 0;
  font-size: 28px;
  line-height: 1.12;
  letter-spacing: 0;
}

.iris-kicker,
.iris-ring-meta {
  margin: 0 0 8px;
  color: var(--iris-cyan);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0;
}

.iris-status {
  color: var(--iris-muted);
  font-size: 15px;
}

.iris-results {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.iris-ring-card,
.iris-center-card,
.iris-empty {
  border: 1px solid var(--iris-line);
  border-radius: 8px;
  background: var(--iris-panel);
  padding: 14px;
}

.iris-ring-card h3,
.iris-center-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  line-height: 1.25;
  letter-spacing: 0;
}

.iris-ring-card p,
.iris-alt,
.iris-center-card dd {
  margin: 0;
  color: var(--iris-muted);
  line-height: 1.4;
}

.iris-alt {
  margin-bottom: 10px;
}

.iris-alt span {
  display: block;
  color: var(--iris-gold);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0;
}

.iris-center-card {
  grid-column: 1 / -1;
  background: var(--iris-panel-2);
  border-color: rgba(159, 232, 112, 0.34);
}

.iris-center-card dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 12px 0 0;
}

.iris-center-card dt {
  color: var(--iris-green);
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 800;
}

.iris-empty {
  grid-column: 1 / -1;
  min-height: 96px;
  display: grid;
  place-items: center;
  color: var(--iris-muted);
}

.status-error .iris-status,
.status-error .iris-kicker {
  color: var(--iris-red);
}

@keyframes iris-pulse {
  0%, 100% { opacity: 0.52; transform: translate(-50%, -50%) scale(0.9); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.12); }
}

@keyframes iris-ring-breathe {
  0%, 100% { box-shadow: 0 0 14px rgba(110, 231, 249, 0.08); }
  50% { box-shadow: 0 0 34px rgba(110, 231, 249, 0.22); }
}

@media (max-width: 860px) {
  .gradio-container {
    padding: 10px !important;
  }

  .iris-visual-grid,
  .iris-results,
  .iris-center-card dl {
    grid-template-columns: 1fr;
  }

  .iris-visual {
    min-height: auto;
  }

  .iris-orbit {
    width: min(100%, 330px);
  }

  .iris-readout h2 {
    font-size: 22px;
  }
}
"""
