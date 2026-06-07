"""Gradio interface for Iris."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Iterable

from iris.engine import IrisEngine, PressureResult
from iris.errors import IrisError
from iris.seeds import DEFAULT_IDEAS


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


def create_app():
    import gradio as gr

    with gr.Blocks(
        title="Iris",
        css=APP_CSS,
        analytics_enabled=False,
    ) as demo:
        gr.HTML(
            render_spiral_html(SpiralView(idea=DEFAULT_IDEAS[0], rings=[])),
            elem_id="iris-stage",
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


def render_spiral_html(view: SpiralView) -> str:
    depth = len(view.rings)
    status_text = escape(view.message or default_message(view))
    title_html = render_primary_title(view)
    subtitle_html = render_primary_subtitle(view)
    electrons_html = render_electron_shell(view)
    context_html = render_context_panel(view)
    depth_text = "READY" if depth == 0 else f"LEVEL {depth}"

    return f"""
<section class="iris-spatial status-{escape(view.status)}">
  <header class="iris-topbar" aria-label="Iris navigation">
    <div class="iris-wordmark">IRIS</div>
    <nav class="iris-nav-links" aria-label="Primary">
      <span class="is-active">Deep Scan</span>
      <span>Orbital Hub</span>
      <span>Neural Link</span>
      <span>Archive</span>
    </nav>
    <div class="iris-top-actions" aria-label="System controls">
      <button type="button" aria-label="Settings"><span></span></button>
      <button type="button" aria-label="Profile"><span></span></button>
    </div>
  </header>

  <aside class="iris-rail" aria-label="Depth rail">
    <div class="iris-rail-item is-current"><span></span><strong>Core</strong></div>
    <div class="iris-rail-item"><span></span><strong>Mantle</strong></div>
    <div class="iris-rail-item"><span></span><strong>Outer Rim</strong></div>
    <div class="iris-rail-item"><span></span><strong>Void</strong></div>
    <div class="iris-rail-meter"><i></i><strong>14.2k</strong></div>
  </aside>

  <main class="iris-canvas" aria-label="Iris spatial canvas">
    {render_orbit_rings()}
    {render_stardust()}

    <div class="iris-nucleus-wrap">
      <div class="iris-nucleus-halo" aria-hidden="true"></div>
      <button class="iris-nucleus" type="button" aria-label="Initiate scan">
        <span class="iris-core-symbol" aria-hidden="true"><i></i></span>
        <span class="iris-core-label">Initiate Scan</span>
      </button>
      <div class="iris-data-chip iris-chip-status">STATUS: {status_text}</div>
      <div class="iris-data-chip iris-chip-latency">DEPTH: {escape(depth_text)}</div>
      {electrons_html}
    </div>

    <div class="iris-hero-copy">
      {title_html}
      {subtitle_html}
    </div>

    {context_html}
  </main>
</section>
"""


def render_primary_title(view: SpiralView) -> str:
    if view.center is not None:
        return f"<h1>{escape(view.center.next_step)}</h1>"
    if view.rings:
        latest = view.rings[-1]
        return f"<h1>{escape(latest.pressure)}</h1>"
    return "<h1>The universe is waiting for your input.</h1>"


def render_primary_subtitle(view: SpiralView) -> str:
    if view.center is not None:
        return '<p class="iris-hero-label">Center point reached.</p>'
    if view.rings:
        latest = view.rings[-1]
        return f'<p class="iris-hero-label">{escape(latest.why_it_bites)}</p>'
    return '<p class="iris-hero-label">Deploy neural probes to map conceptual space.</p>'


def render_electron_shell(view: SpiralView) -> str:
    if not view.rings and view.pending_depth is None and not view.center_pending:
        return ""

    nodes = list(view.rings)
    if view.pending_depth is not None:
        nodes.append(
            RingView(
                depth=view.pending_depth,
                pressure=f"{ring_name(view.pending_depth)} forming",
                why_it_bites="",
            )
        )
    if view.center_pending:
        nodes.append(RingView(depth=RINGS + 1, pressure="Center forming", why_it_bites=""))

    positions = ("a", "b", "c", "d", "e")
    items = []
    for index, ring in enumerate(nodes[:5]):
        label = "CENTER" if ring.depth > RINGS else f"R{ring.depth}"
        title = escape(ring.pressure)
        items.append(
            f"""
      <button class="iris-electron iris-electron-{positions[index]}" type="button">
        <span>{escape(label)}</span>
        <small>{title}</small>
      </button>
"""
        )
    return f'<div class="iris-electron-shell" aria-label="Pressure electrons">{"".join(items)}</div>'


def render_context_panel(view: SpiralView) -> str:
    if not view.idea and not view.rings and view.center is None:
        return ""

    idea = escape(view.idea or "Awaiting idea")
    if view.center is not None:
        body = escape(view.center.assumption_to_test)
        eyebrow = "CENTER ASSUMPTION"
    elif view.rings:
        latest = view.rings[-1]
        body = escape(latest.alternative or latest.why_it_bites)
        eyebrow = f"{ring_name(latest.depth).upper()} SIGNAL"
    else:
        body = "Ready to receive a raw idea."
        eyebrow = "NEURAL TELEMETRY"

    return f"""
    <aside class="iris-context-panel">
      <span>{escape(eyebrow)}</span>
      <p>{body}</p>
      <dl>
        <div><dt>Input</dt><dd>{idea}</dd></div>
        <div><dt>Protocol</dt><dd>MiniCPM local</dd></div>
      </dl>
    </aside>
"""


def render_orbit_rings() -> str:
    return """
    <div class="iris-orbit-ring iris-orbit-ring-1"></div>
    <div class="iris-orbit-ring iris-orbit-ring-2"></div>
    <div class="iris-orbit-ring iris-orbit-ring-3"></div>
    <div class="iris-orbit-ring iris-orbit-ring-4"></div>
    <div class="iris-orbit-ring iris-orbit-ring-5"></div>
"""


def render_stardust() -> str:
    stars = []
    points = (
        (18, 22),
        (31, 30),
        (46, 17),
        (70, 25),
        (85, 39),
        (25, 53),
        (41, 68),
        (62, 55),
        (77, 72),
        (91, 82),
        (15, 78),
        (54, 86),
        (68, 12),
        (35, 88),
        (93, 18),
    )
    for index, (left, top) in enumerate(points):
        size = "is-large" if index % 5 == 0 else ""
        stars.append(
            f'<span class="{size}" style="left:{left}%; top:{top}%"></span>'
        )
    return f'<div class="iris-stardust" aria-hidden="true">{"".join(stars)}</div>'


def default_message(view: SpiralView) -> str:
    if view.status == "complete":
        return "Center reached."
    if view.status == "running":
        return "Mapping."
    if view.status == "error":
        return "Signal interrupted."
    return "Idle"


APP_CSS = """
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&family=JetBrains+Mono:wght@400;500&display=swap");

:root {
  --iris-void: #050508;
  --iris-bg: #13131b;
  --iris-surface: rgba(19, 19, 27, 0.42);
  --iris-surface-strong: rgba(31, 31, 39, 0.52);
  --iris-line: rgba(180, 203, 206, 0.18);
  --iris-line-faint: rgba(180, 203, 206, 0.08);
  --iris-text: #e4e1ed;
  --iris-muted: #bac9cc;
  --iris-cyan: #00daf3;
  --iris-cyan-soft: #9cf0ff;
}

* {
  box-sizing: border-box;
  letter-spacing: 0;
}

body,
.gradio-container {
  margin: 0 !important;
  background: var(--iris-void) !important;
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

.iris-spatial {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(0, 218, 243, 0.08), transparent 18%),
    radial-gradient(circle at 50% 52%, rgba(19, 19, 27, 0.38), transparent 36%),
    var(--iris-void);
}

.iris-topbar {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 20;
  width: 100%;
  height: 80px;
  display: grid;
  grid-template-columns: 220px 1fr 220px;
  align-items: center;
  padding: 0 40px;
  border-bottom: 1px solid var(--iris-line);
  background: rgba(19, 19, 27, 0.42);
  backdrop-filter: blur(20px);
}

.iris-wordmark {
  color: var(--iris-cyan);
  font-size: 32px;
  font-weight: 300;
  line-height: 1;
  text-shadow: 0 0 18px rgba(0, 218, 243, 0.55);
}

.iris-nav-links {
  display: flex;
  justify-content: center;
  gap: 40px;
  color: var(--iris-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.iris-nav-links span {
  padding: 4px 0 8px;
  border-bottom: 1px solid transparent;
}

.iris-nav-links .is-active {
  color: var(--iris-cyan-soft);
  border-bottom-color: var(--iris-cyan);
}

.iris-top-actions {
  display: flex;
  justify-content: flex-end;
  gap: 18px;
}

.iris-top-actions button {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: var(--iris-muted);
  background: transparent;
}

.iris-top-actions button span {
  width: 22px;
  height: 22px;
  border: 2px solid currentColor;
  border-radius: 50%;
  position: relative;
}

.iris-top-actions button:first-child span::before,
.iris-top-actions button:first-child span::after {
  content: "";
  position: absolute;
  inset: 8px -5px;
  border-top: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
}

.iris-top-actions button:first-child span::after {
  transform: rotate(90deg);
}

.iris-top-actions button:last-child span::before {
  content: "";
  position: absolute;
  top: 4px;
  left: 7px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.iris-top-actions button:last-child span::after {
  content: "";
  position: absolute;
  left: 4px;
  bottom: 3px;
  width: 12px;
  height: 7px;
  border: 2px solid currentColor;
  border-radius: 50% 50% 0 0;
  border-bottom: 0;
}

.iris-rail {
  position: absolute;
  top: 80px;
  left: 0;
  bottom: 0;
  z-index: 18;
  width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 52px;
  padding: 32px 0 26px;
  border-right: 1px solid rgba(180, 203, 206, 0.1);
  background: rgba(13, 13, 21, 0.22);
  backdrop-filter: blur(18px);
}

.iris-rail-item {
  display: grid;
  place-items: center;
  gap: 8px;
  color: rgba(186, 201, 204, 0.62);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 10px;
  font-weight: 500;
  text-align: center;
}

.iris-rail-item span {
  width: 42px;
  height: 42px;
  display: block;
  border: 1px solid transparent;
  border-radius: 50%;
  position: relative;
}

.iris-rail-item span::before,
.iris-rail-item span::after {
  content: "";
  position: absolute;
  inset: 12px;
  border: 2px solid currentColor;
  border-radius: 50%;
}

.iris-rail-item span::after {
  inset: 17px;
  background: currentColor;
}

.iris-rail-item.is-current {
  color: var(--iris-cyan-soft);
}

.iris-rail-item.is-current span {
  border-color: rgba(156, 240, 255, 0.55);
  background: rgba(0, 218, 243, 0.1);
  box-shadow: 0 0 22px rgba(0, 218, 243, 0.18);
}

.iris-rail-meter {
  margin-top: auto;
  display: grid;
  place-items: center;
  gap: 9px;
  color: var(--iris-cyan-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 10px;
}

.iris-rail-meter i {
  width: 34px;
  height: 34px;
  display: block;
  border-radius: 50%;
  border: 1px solid rgba(0, 218, 243, 0.42);
  background:
    radial-gradient(circle at 45% 45%, rgba(156, 240, 255, 0.82), transparent 8%),
    radial-gradient(circle at center, rgba(0, 218, 243, 0.2), rgba(19, 19, 27, 0.65));
}

.iris-canvas {
  position: relative;
  min-height: 100vh;
  padding: 80px 40px 54px 80px;
  display: grid;
  place-items: center;
}

.iris-orbit-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px solid var(--iris-line-faint);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.iris-orbit-ring-1 { width: 280px; height: 280px; opacity: 0.95; }
.iris-orbit-ring-2 { width: 500px; height: 500px; opacity: 0.62; }
.iris-orbit-ring-3 { width: 760px; height: 760px; opacity: 0.42; }
.iris-orbit-ring-4 { width: 1080px; height: 1080px; opacity: 0.28; }
.iris-orbit-ring-5 { width: 1420px; height: 1420px; opacity: 0.18; }

.iris-stardust {
  position: absolute;
  inset: 80px 0 0 80px;
  pointer-events: none;
}

.iris-stardust span {
  position: absolute;
  width: 2px;
  height: 2px;
  display: block;
  border-radius: 50%;
  background: rgba(0, 218, 243, 0.62);
}

.iris-stardust .is-large {
  width: 3px;
  height: 3px;
  background: rgba(186, 201, 204, 0.58);
}

.iris-nucleus-wrap {
  position: relative;
  z-index: 5;
  width: 320px;
  height: 320px;
  display: grid;
  place-items: center;
  transform: translateY(-28px);
}

.iris-nucleus-halo {
  position: absolute;
  inset: -66px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 218, 243, 0.16), transparent 60%);
  filter: blur(12px);
}

.iris-nucleus {
  position: relative;
  z-index: 2;
  width: 256px;
  height: 256px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(180, 203, 206, 0.24);
  border-radius: 50%;
  background: rgba(19, 19, 27, 0.42);
  backdrop-filter: blur(20px);
  color: var(--iris-text);
  box-shadow:
    0 0 60px rgba(0, 218, 243, 0.28),
    inset 0 0 22px rgba(0, 218, 243, 0.16);
}

.iris-core-symbol {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  margin-bottom: 12px;
  border: 4px solid var(--iris-cyan-soft);
  border-radius: 50%;
  box-shadow: 0 0 24px rgba(156, 240, 255, 0.5);
}

.iris-core-symbol i {
  width: 16px;
  height: 16px;
  display: block;
  border-radius: 50%;
  background: var(--iris-cyan-soft);
}

.iris-core-label {
  color: var(--iris-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.iris-data-chip {
  position: absolute;
  z-index: 4;
  min-width: 124px;
  padding: 6px 13px;
  border: 1px solid rgba(180, 203, 206, 0.24);
  border-radius: 999px;
  background: rgba(19, 19, 27, 0.48);
  color: var(--iris-cyan-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  white-space: nowrap;
  backdrop-filter: blur(18px);
}

.iris-chip-status {
  top: 50px;
  right: -88px;
}

.iris-chip-latency {
  bottom: 54px;
  left: -86px;
  color: var(--iris-muted);
}

.iris-electron-shell {
  position: absolute;
  inset: 0;
  z-index: 6;
  pointer-events: none;
}

.iris-electron {
  position: absolute;
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(0, 218, 243, 0.7);
  border-radius: 50%;
  background: rgba(0, 218, 243, 0.12);
  color: var(--iris-cyan-soft);
  box-shadow: 0 0 20px rgba(0, 218, 243, 0.28);
  pointer-events: auto;
}

.iris-electron span {
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 10px;
}

.iris-electron small {
  position: absolute;
  top: 58px;
  left: 50%;
  max-width: 220px;
  padding: 6px 10px;
  border: 1px solid rgba(180, 203, 206, 0.2);
  border-radius: 999px;
  background: rgba(31, 31, 39, 0.72);
  color: var(--iris-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 10px;
  line-height: 1.3;
  text-align: center;
  transform: translateX(-50%);
}

.iris-electron-a { top: 2px; left: 50%; transform: translateX(-50%); }
.iris-electron-b { top: 98px; right: -6px; }
.iris-electron-c { bottom: 22px; right: 40px; }
.iris-electron-d { bottom: 22px; left: 40px; }
.iris-electron-e { top: 98px; left: -6px; }

.iris-hero-copy {
  position: absolute;
  left: 50%;
  bottom: 64px;
  z-index: 8;
  width: min(680px, calc(100vw - 160px));
  text-align: center;
  transform: translateX(-50%);
}

.iris-hero-copy h1 {
  margin: 0;
  color: var(--iris-text);
  font-size: 48px;
  font-weight: 300;
  line-height: 1.12;
}

.iris-hero-label {
  margin: 16px auto 0;
  color: var(--iris-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  text-transform: uppercase;
}

.iris-context-panel {
  position: absolute;
  right: 40px;
  top: 130px;
  z-index: 9;
  width: 310px;
  padding: 24px;
  border: 1px solid var(--iris-line);
  border-radius: 32px;
  background: rgba(19, 19, 27, 0.38);
  backdrop-filter: blur(20px);
}

.iris-context-panel span,
.iris-context-panel dt {
  color: var(--iris-cyan-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.iris-context-panel p {
  margin: 18px 0 22px;
  color: var(--iris-text);
  font-size: 15px;
  line-height: 1.55;
}

.iris-context-panel dl {
  margin: 0;
  display: grid;
  gap: 12px;
}

.iris-context-panel div {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr);
  gap: 12px;
  border-top: 1px solid rgba(180, 203, 206, 0.1);
  padding-top: 12px;
}

.iris-context-panel dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--iris-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 11px;
  line-height: 1.4;
}

.status-ready .iris-context-panel {
  display: none;
}

.status-error .iris-data-chip {
  color: #ffb4ab;
  border-color: rgba(255, 180, 171, 0.34);
}

@media (max-width: 900px) {
  .iris-topbar {
    height: 72px;
    grid-template-columns: 1fr auto;
    padding: 0 20px;
  }

  .iris-nav-links,
  .iris-top-actions {
    display: none;
  }

  .iris-rail {
    display: none;
  }

  .iris-canvas {
    padding: 72px 20px 40px;
  }

  .iris-nucleus-wrap {
    width: 260px;
    height: 260px;
    transform: translateY(-14px);
  }

  .iris-nucleus {
    width: 210px;
    height: 210px;
  }

  .iris-orbit-ring-1 { width: 260px; height: 260px; }
  .iris-orbit-ring-2 { width: 420px; height: 420px; }
  .iris-orbit-ring-3 { width: 620px; height: 620px; }
  .iris-orbit-ring-4 { width: 860px; height: 860px; }
  .iris-orbit-ring-5 { width: 1100px; height: 1100px; }

  .iris-chip-status {
    top: 24px;
    right: -42px;
  }

  .iris-chip-latency {
    bottom: 30px;
    left: -42px;
  }

  .iris-hero-copy {
    bottom: 42px;
    width: min(520px, calc(100vw - 40px));
  }

  .iris-hero-copy h1 {
    font-size: 34px;
  }

  .iris-context-panel {
    display: none;
  }
}

@media (max-width: 520px) {
  .iris-wordmark {
    font-size: 28px;
  }

  .iris-nucleus-wrap {
    width: 220px;
    height: 220px;
  }

  .iris-nucleus {
    width: 184px;
    height: 184px;
  }

  .iris-core-symbol {
    width: 42px;
    height: 42px;
  }

  .iris-data-chip {
    position: static;
    margin-top: 10px;
    text-align: center;
  }

  .iris-chip-latency {
    display: none;
  }

  .iris-hero-copy h1 {
    font-size: 28px;
  }

  .iris-hero-label {
    font-size: 10px;
  }
}
"""
