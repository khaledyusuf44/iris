# Project Brief

## Name

Iris

## Status

Day 2 UI and submission polish. The Day 1 constraint engine has passed its
quality gate, and Iris now has a live Gradio canvas UI.

## Current Objective

Turn the validated local MiniCPM pressure engine into a polished,
screen-recordable hackathon app: click a canvas, type an idea, receive four
sharp pressure directions, and write the next sharper iteration.

## Open Questions

- Should the submitted local model path stay on Ollama, or can MiniCPM move to
  llama.cpp cleanly for an extra badge?
- Should the custom UI remain embedded HTML/CSS/JS in Gradio, or move to a
  `gr.Server` frontend if that improves Hugging Face Spaces deployment?
- What demo idea best shows four sharp pressures and a stronger second
  iteration?
- What video and social post links will be added to the README for submission?

## Immediate Next Step

Continue polishing the canvas flow for the demo video, then prepare Hugging
Face Space deployment under the hackathon organization.
