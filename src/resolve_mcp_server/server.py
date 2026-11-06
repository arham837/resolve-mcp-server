"""FastMCP server exposing DaVinci Resolve Studio tools to MCP clients."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from resolve_mcp_server.resolve_client import ResolveController

mcp = FastMCP(
    "DaVinci Resolve Studio MCP Server",
    instructions=(
        "Interact with an active DaVinci Resolve Studio session to inspect projects, "
        "timelines, clips, markers, media pool items, and render jobs."
    ),
)

_controller = ResolveController()


def get_controller() -> ResolveController:
    """Return the active ResolveController instance (replaceable in tests)."""
    return _controller


def set_controller(controller: ResolveController) -> None:
    """Override the ResolveController instance (useful for unit testing)."""
    global _controller
    _controller = controller


@mcp.tool()
def get_project_info() -> str:
    """Get metadata for the active DaVinci Resolve project (name, FPS, resolution, active timeline)."""
    data = get_controller().get_project_info()
    return json.dumps(data, indent=2)


@mcp.tool()
def list_timelines() -> str:
    """List all timelines in the active DaVinci Resolve project and show which one is active."""
    data = get_controller().list_timelines()
    return json.dumps(data, indent=2)


@mcp.tool()
def set_current_timeline(timeline_name: str) -> str:
    """Switch the active timeline in DaVinci Resolve by its exact name."""
    data = get_controller().set_current_timeline(timeline_name)
    return json.dumps(data, indent=2)


@mcp.tool()
def get_timeline_details() -> str:
    """Get track counts, start/end frames, start timecode, and markers for the active timeline."""
    data = get_controller().get_timeline_details()
    return json.dumps(data, indent=2)


@mcp.tool()
def list_timeline_clips(track_type: str = "video", track_index: int = 1) -> str:
    """List all clips on a specific track ('video', 'audio', or 'subtitle') and 1-based track index."""
    data = get_controller().list_timeline_clips(track_type=track_type, track_index=track_index)
    return json.dumps(data, indent=2)


@mcp.tool()
def add_timeline_marker(
    frame_id: int,
    color: str = "Blue",
    name: str = "AI Marker",
    note: str = "",
    duration: int = 1,
    custom_data: str = "",
) -> str:
    """Add a color-coded marker to the active timeline at a specific frame offset."""
    data = get_controller().add_timeline_marker(
        frame_id=frame_id,
        color=color,
        name=name,
        note=note,
        duration=duration,
        custom_data=custom_data,
    )
    return json.dumps(data, indent=2)


@mcp.tool()
def delete_timeline_markers_by_color(color: str = "All") -> str:
    """Delete markers on the active timeline matching a specific color (or 'All')."""
    data = get_controller().delete_timeline_markers_by_color(color=color)
    return json.dumps(data, indent=2)


@mcp.tool()
def list_media_pool_clips() -> str:
    """List all clips inside the currently selected Media Pool bin/folder."""
    data = get_controller().list_media_pool_clips()
    return json.dumps(data, indent=2)


@mcp.tool()
def import_media(file_paths: list[str]) -> str:
    """Import one or more local media files into the active Media Pool folder."""
    data = get_controller().import_media(file_paths=file_paths)
    return json.dumps(data, indent=2)


@mcp.tool()
def create_timeline_from_clips(timeline_name: str) -> str:
    """Create a new timeline from the clips in the current Media Pool folder (or an empty timeline if none)."""
    data = get_controller().create_timeline_from_clips(timeline_name=timeline_name)
    return json.dumps(data, indent=2)


@mcp.tool()
def start_render(
    preset_name: str | None = None,
    target_dir: str | None = None,
    custom_name: str | None = None,
) -> str:
    """Queue and start a render job for the active timeline with optional preset and output directory."""
    data = get_controller().start_render(
        preset_name=preset_name,
        target_dir=target_dir,
        custom_name=custom_name,
    )
    return json.dumps(data, indent=2)


def main() -> None:
    """Run the DaVinci Resolve MCP server over standard I/O."""
    mcp.run()


if __name__ == "__main__":
    main()
