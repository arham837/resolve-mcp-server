"""Unit tests for resolve-mcp-server using a mocked DaVinci Resolve Studio API."""

from __future__ import annotations

from typing import Any
import unittest

from resolve_mcp_server.resolve_client import ResolveController


class FakeClipItem:
    def __init__(self, name: str, start: int = 0, end: int = 100) -> None:
        self._name = name
        self._start = start
        self._end = end

    def GetName(self) -> str:
        return self._name

    def GetStart(self) -> int:
        return self._start

    def GetEnd(self) -> int:
        return self._end

    def GetDuration(self) -> int:
        return self._end - self._start

    def GetLeftOffset(self) -> int:
        return 0

    def GetRightOffset(self) -> int:
        return 0

    def GetClipProperty(self) -> dict[str, Any]:
        return {
            "FPS": "24.0",
            "Resolution": "3840x2160",
            "Duration": "00:00:04:04",
            "Type": "Video + Audio",
        }


class FakeTimeline:
    def __init__(self, name: str = "Main Edit") -> None:
        self._name = name
        self._markers: dict[int, dict[str, Any]] = {}

    def GetName(self) -> str:
        return self._name

    def GetStartFrame(self) -> int:
        return 86400

    def GetEndFrame(self) -> int:
        return 87400

    def GetStartTimecode(self) -> str:
        return "01:00:00:00"

    def GetTrackCount(self, track_type: str) -> int:
        counts = {"video": 2, "audio": 3, "subtitle": 1}
        return counts.get(track_type, 0)

    def GetItemListInTrack(self, track_type: str, track_index: int) -> list[FakeClipItem]:
        if track_type == "video" and track_index == 1:
            return [FakeClipItem("A001_C001.mov", 86400, 86640)]
        return []

    def GetMarkers(self) -> dict[int, dict[str, Any]]:
        return self._markers

    def AddMarker(
        self,
        frame_id: int,
        color: str,
        name: str,
        note: str,
        duration: int,
        custom_data: str = "",
    ) -> bool:
        self._markers[frame_id] = {
            "color": color,
            "name": name,
            "note": note,
            "duration": duration,
            "customData": custom_data,
        }
        return True

    def DeleteMarkersByColor(self, color: str) -> bool:
        if color == "All":
            self._markers.clear()
        else:
            self._markers = {
                k: v for k, v in self._markers.items() if v.get("color") != color
            }
        return True


class FakeFolder:
    def __init__(self) -> None:
        self._clips = [FakeClipItem("A001_C001.mov"), FakeClipItem("B002_C005.mov")]

    def GetName(self) -> str:
        return "Master"

    def GetClipList(self) -> list[FakeClipItem]:
        return self._clips


class FakeMediaPool:
    def __init__(self) -> None:
        self._folder = FakeFolder()

    def GetCurrentFolder(self) -> FakeFolder:
        return self._folder

    def ImportMedia(self, file_paths: list[str]) -> list[FakeClipItem]:
        return [FakeClipItem(path.split("/")[-1]) for path in file_paths]

    def CreateTimelineFromClips(self, name: str, clips: list[FakeClipItem]) -> FakeTimeline:
        return FakeTimeline(name=name)

    def CreateEmptyTimeline(self, name: str) -> FakeTimeline:
        return FakeTimeline(name=name)


class FakeProject:
    def __init__(self) -> None:
        self._timelines = [FakeTimeline("Main Edit"), FakeTimeline("Social Cut")]
        self._current_timeline = self._timelines[0]
        self._media_pool = FakeMediaPool()

    def GetName(self) -> str:
        return "Documentary Feature"

    def GetTimelineCount(self) -> int:
        return len(self._timelines)

    def GetCurrentTimeline(self) -> FakeTimeline:
        return self._current_timeline

    def GetTimelineByIndex(self, idx: int) -> FakeTimeline:
        return self._timelines[idx - 1]

    def SetCurrentTimeline(self, timeline: FakeTimeline) -> bool:
        self._current_timeline = timeline
        return True

    def GetSetting(self, key: str) -> str:
        settings = {
            "timelineFrameRate": "24",
            "timelineResolutionWidth": "3840",
            "timelineResolutionHeight": "2160",
        }
        return settings.get(key, "")

    def GetMediaPool(self) -> FakeMediaPool:
        return self._media_pool

    def LoadRenderPreset(self, preset_name: str) -> bool:
        return True

    def SetRenderSettings(self, settings: dict[str, Any]) -> bool:
        return True

    def AddRenderJob(self) -> str:
        return "job-001"

    def StartRendering(self, job_id: str | None = None) -> bool:
        return True

    def IsRenderingInProgress(self) -> bool:
        return True


class FakeProjectManager:
    def __init__(self) -> None:
        self._project = FakeProject()

    def GetCurrentProject(self) -> FakeProject:
        return self._project


class FakeResolve:
    def __init__(self) -> None:
        self._pm = FakeProjectManager()

    def GetProjectManager(self) -> FakeProjectManager:
        return self._pm


class ResolveControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ResolveController(resolve_instance=FakeResolve())

    def test_get_project_info(self) -> None:
        info = self.controller.get_project_info()
        self.assertEqual(info["project_name"], "Documentary Feature")
        self.assertEqual(info["timeline_count"], 2)
        self.assertEqual(info["current_timeline"], "Main Edit")

    def test_list_and_switch_timelines(self) -> None:
        timelines = self.controller.list_timelines()
        self.assertEqual(len(timelines), 2)
        res = self.controller.set_current_timeline("Social Cut")
        self.assertTrue(res["success"])
        self.assertEqual(self.controller.get_project_info()["current_timeline"], "Social Cut")

    def test_markers_workflow(self) -> None:
        marker = self.controller.add_timeline_marker(
            frame_id=86500, color="Red", name="Fix Color", note="Check skin tones", duration=12
        )
        self.assertTrue(marker["success"])
        details = self.controller.get_timeline_details()
        self.assertIn(86500, details["markers"])

        deleted = self.controller.delete_timeline_markers_by_color("Red")
        self.assertTrue(deleted["success"])
        self.assertEqual(self.controller.get_timeline_details()["markers"], {})

    def test_media_pool_and_render(self) -> None:
        clips = self.controller.list_media_pool_clips()
        self.assertEqual(len(clips), 2)

        imported = self.controller.import_media(["/footage/interview.mov"])
        self.assertEqual(imported["imported_count"], 1)

        created = self.controller.create_timeline_from_clips("Assembly Cut")
        self.assertTrue(created["success"])

        render = self.controller.start_render(preset_name="H.264 Master", target_dir="/renders")
        self.assertTrue(render["success"])
        self.assertEqual(render["job_id"], "job-001")


if __name__ == "__main__":
    unittest.main()
