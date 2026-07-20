"""Minimal RenderNode union for RenderedEntry.body (TASK-H006).

ARCHITECTURE.md 16 references `RenderNode` as the element type of
`RenderedEntry.body` but does not specify its shape. This starts with the
minimum needed to represent plain text (ARCHITECTURE.md 16.2's rendered
layout is plain text with line breaks); TASK-H007 (Mini layout renderer)
extends this union as it discovers what else the layout needs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextRenderNode:
    """A run of rendered text."""

    text: str


@dataclass(frozen=True, slots=True)
class LineBreakRenderNode:
    """An explicit line break between rendered sections."""


@dataclass(frozen=True, slots=True)
class LinkRenderNode:
    """A visible inline label referencing another rendered entry."""

    label: str
    target: str


@dataclass(frozen=True, slots=True)
class GraphicRenderNode:
    """A color graphic registered in the FreePWING graphics catalog."""

    name: str


RenderNode = TextRenderNode | LineBreakRenderNode | LinkRenderNode | GraphicRenderNode
