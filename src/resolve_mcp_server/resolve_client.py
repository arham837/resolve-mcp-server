"""Wrapper for connecting to the DaVinci Resolve Studio Scripting API."""

from __future__ import annotations

import importlib.util
import os
import platform
import sys
from pathlib import Path
from typing import Any


VALID_MARKER_COLORS = {
    "Blue",
    "Cyan",
    "Green",
    "Yellow",
    "Red",
    "Pink",
    "Purple",
    "Fuchsia",
    "Rose",
    "Lavender",
    "Sky",
    "Mint",
    "Lemon",
    "Sand",
    "Cocoa",
    "Cream",
}


class ResolveConnectionError(RuntimeError):
    """Raised when DaVinci Resolve Studio cannot be reached via the Scripting API."""


def _configure_resolve_env() -> str:
    """Configure platform-specific paths for DaVinci Resolve scripting and return module path."""
    system = platform.system()
    if system == "Darwin":
        default_api = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        default_lib = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
    elif system == "Windows":
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        default_api = os.path.join(
            program_data,
            "Blackmagic Design",
            "DaVinci Resolve",
            "Support",
            "Developer",
            "Scripting",
        )
        default_lib = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
    else:
        default_api = "/opt/resolve/Developer/Scripting"
        default_lib = "/opt/resolve/libs/Fusion/fusionscript.so"

    script_api = os.environ.setdefault("RESOLVE_SCRIPT_API", default_api)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", default_lib)

    modules_dir = os.path.join(script_api, "Modules")
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
    return modules_dir


def load_resolve_instance() -> Any:
    """Load the DaVinciResolveScript module and return an active Resolve app handle."""
    modules_dir = _configure_resolve_env()
    try:
        import DaVinciResolveScript as bmd  # type: ignore[import-not-found]
    except ImportError:
        module_file = Path(modules_dir) / "DaVinciResolveScript.py"
        if not module_file.exists():
            raise ResolveConnectionError(
                f"Could not find DaVinciResolveScript.py in '{modules_dir}'. "
                "Verify DaVinci Resolve Studio 18+ is installed and RESOLVE_SCRIPT_API is set."
            )
        spec = importlib.util.spec_from_file_location("DaVinciResolveScript", module_file)
        if spec is None or spec.loader is None:
            raise ResolveConnectionError("Failed to load DaVinciResolveScript module spec.")
        bmd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bmd)

    resolve = bmd.scriptapp("Resolve")
    if resolve is None:
        raise ResolveConnectionError(
            "Unable to connect to DaVinci Resolve Studio. Make sure DaVinci Resolve Studio is "
            "running and 'External scripting using: Local' is enabled in Preferences > System > General."
        )
    return resolve


class ResolveController:
    """High-level helper wrapping DaVinci Resolve Studio project, timeline, and media actions."""

    def __init__(self, resolve_instance: Any | None = None) -> None:
        self._resolve = resolve_instance

    @property
    def resolve(self) -> Any:
        if self._resolve is None:
            self._resolve = load_resolve_instance()
        return self._resolve

    def _get_project(self) -> Any:
        pm = self.resolve.GetProjectManager()
        if pm is None:
            raise ResolveConnectionError("Failed to retrieve ProjectManager from DaVinci Resolve.")
        project = pm.GetCurrentProject()
        if project is None:
            raise ResolveConnectionError("No active project is currently open in DaVinci Resolve.")
        return project

    def _get_timeline(self) -> tuple[Any, Any]:
        project = self._get_project()
        timeline = project.GetCurrentTimeline()
        if timeline is None:
            raise ResolveConnectionError("No active timeline is currently open in the project.")
        return project, timeline

    def get_project_info(self) -> dict[str, Any]:
        project = self._get_project()
        current_timeline = project.GetCurrentTimeline()
        return {
            "project_name": project.GetName(),
            "timeline_count": project.GetTimelineCount(),
            "current_timeline": current_timeline.GetName() if current_timeline else None,
            "frame_rate": project.GetSetting("timelineFrameRate"),
            "resolution_width": project.GetSetting("timelineResolutionWidth"),
            "resolution_height": project.GetSetting("timelineResolutionHeight"),
        }

    def list_timelines(self) -> list[dict[str, Any]]:
        project = self._get_project()
        count = int(project.GetTimelineCount() or 0)
        current = project.GetCurrentTimeline()
        current_name = current.GetName() if current else None

        timelines: list[dict[str, Any]] = []
        for idx in range(1, count + 1):
            tl = project.GetTimelineByIndex(idx)
            if tl is not None:
                name = tl.GetName()
                timelines.append(
                    {
                        "index": idx,
                        "name": name,
                        "is_active": name == current_name,
                        "start_frame": tl.GetStartFrame(),
                        "end_frame": tl.GetEndFrame(),
                    }
                )
        return timelines

    def set_current_timeline(self, timeline_name: str) -> dict[str, Any]:
        project = self._get_project()
        count = int(project.GetTimelineCount() or 0)
        for idx in range(1, count + 1):
            tl = project.GetTimelineByIndex(idx)
            if tl is not None and tl.GetName() == timeline_name:
                success = bool(project.SetCurrentTimeline(tl))
                return {
                    "success": success,
                    "active_timeline": timeline_name if success else None,
                }
        raise ValueError(f"Timeline '{timeline_name}' was not found in project '{project.GetName()}'.")

    def get_timeline_details(self) -> dict[str, Any]:
        _, timeline = self._get_timeline()
        markers = timeline.GetMarkers() or {}
        return {
            "name": timeline.GetName(),
            "start_frame": timeline.GetStartFrame(),
            "end_frame": timeline.GetEndFrame(),
            "start_timecode": timeline.GetStartTimecode(),
            "tracks": {
                "video": timeline.GetTrackCount("video"),
                "audio": timeline.GetTrackCount("audio"),
                "subtitle": timeline.GetTrackCount("subtitle"),
            },
            "markers": markers,
        }

    def list_timeline_clips(self, track_type: str = "video", track_index: int = 1) -> list[dict[str, Any]]:
        normalized_type = track_type.lower().strip()
        if normalized_type not in {"video", "audio", "subtitle"}:
            raise ValueError("track_type must be one of 'video', 'audio', or 'subtitle'.")
        if track_index < 1:
            raise ValueError("track_index must be 1 or greater (1-indexed).")

        _, timeline = self._get_timeline()
        items = timeline.GetItemListInTrack(normalized_type, track_index) or []
        clips: list[dict[str, Any]] = []
        for item in items:
            clips.append(
                {
                    "name": item.GetName(),
                    "start_frame": item.GetStart(),
                    "end_frame": item.GetEnd(),
                    "duration": item.GetDuration(),
                    "left_offset": item.GetLeftOffset(),
                    "right_offset": item.GetRightOffset(),
                }
            )
        return clips

    def add_timeline_marker(
        self,
        frame_id: int,
        color: str = "Blue",
        name: str = "AI Marker",
        note: str = "",
        duration: int = 1,
        custom_data: str = "",
    ) -> dict[str, Any]:
        normalized_color = color.capitalize()
        if normalized_color not in VALID_MARKER_COLORS:
            raise ValueError(
                f"Invalid marker color '{color}'. Choose from: {', '.join(sorted(VALID_MARKER_COLORS))}."
            )
        if duration < 1:
            raise ValueError("Marker duration must be at least 1 frame.")

        _, timeline = self._get_timeline()
        added = bool(
            timeline.AddMarker(frame_id, normalized_color, name, note, duration, custom_data)
        )
        return {
            "success": added,
            "timeline": timeline.GetName(),
            "frame_id": frame_id,
            "color": normalized_color,
            "name": name,
            "note": note,
            "duration": duration,
        }

    def delete_timeline_markers_by_color(self, color: str = "All") -> dict[str, Any]:
        _, timeline = self._get_timeline()
        deleted = bool(timeline.DeleteMarkersByColor(color))
        return {
            "success": deleted,
            "timeline": timeline.GetName(),
            "deleted_color": color,
        }

    def list_media_pool_clips(self) -> list[dict[str, Any]]:
        project = self._get_project()
        media_pool = project.GetMediaPool()
        folder = media_pool.GetCurrentFolder()
        clips = folder.GetClipList() or []
        result: list[dict[str, Any]] = []
        for clip in clips:
            props = clip.GetClipProperty() or {}
            result.append(
                {
                    "name": clip.GetName(),
                    "folder": folder.GetName(),
                    "fps": props.get("FPS"),
                    "resolution": props.get("Resolution"),
                    "duration": props.get("Duration"),
                    "type": props.get("Type"),
                }
            )
        return result

    def import_media(self, file_paths: list[str]) -> dict[str, Any]:
        if not file_paths:
            raise ValueError("file_paths must contain at least one path.")
        project = self._get_project()
        media_pool = project.GetMediaPool()
        imported_items = media_pool.ImportMedia(file_paths) or []
        return {
            "imported_count": len(imported_items),
            "imported_names": [item.GetName() for item in imported_items],
        }

    def create_timeline_from_clips(self, timeline_name: str) -> dict[str, Any]:
        if not timeline_name.strip():
            raise ValueError("timeline_name cannot be empty.")
        project = self._get_project()
        media_pool = project.GetMediaPool()
        folder = media_pool.GetCurrentFolder()
        clips = folder.GetClipList() or []
        if not clips:
            timeline = media_pool.CreateEmptyTimeline(timeline_name)
        else:
            timeline = media_pool.CreateTimelineFromClips(timeline_name, clips)

        if timeline is None:
            raise RuntimeError(f"Failed to create timeline '{timeline_name}'.")
        return {
            "success": True,
            "timeline_name": timeline.GetName(),
            "clip_count": len(clips),
        }

    def start_render(
        self, preset_name: str | None = None, target_dir: str | None = None, custom_name: str | None = None
    ) -> dict[str, Any]:
        project, _ = self._get_timeline()
        if preset_name:
            project.LoadRenderPreset(preset_name)
        render_settings: dict[str, Any] = {}
        if target_dir:
            render_settings["TargetDir"] = target_dir
        if custom_name:
            render_settings["CustomName"] = custom_name
        if render_settings:
            project.SetRenderSettings(render_settings)

        job_id = project.AddRenderJob()
        started = bool(project.StartRendering(job_id)) if job_id else bool(project.StartRendering())
        return {
            "success": started,
            "job_id": job_id,
            "is_rendering": bool(project.IsRenderingInProgress()),
        }
