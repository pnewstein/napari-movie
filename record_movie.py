import napari

import numpy as np

from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, List, Optional, TYPE_CHECKING
import time

import cv2


if TYPE_CHECKING:
    viewer = napari.viewer.Viewer()

@dataclass
class CameraPosition():
    center: Tuple[float, float, float]
    angles: Tuple[float, float, float]
    zoom: float
    perspective: float

    @classmethod
    def fromViewerCamera(cls, camera: napari.components.camera.Camera):
        return cls(
            center = camera.center,
            angles = camera.angles,
            zoom = camera.zoom,
            perspective = camera.perspective,
        )
    
    def set_on_camera(self, camera: napari.components.camera.Camera):
        camera.center = self.center
        camera.angles = self.angles
        camera.zoom = self.zoom
        camera.perspective = self.perspective

camera_view_list: List[CameraPosition] = []

def interpolate_camera_positions(initial_position: CameraPosition, end_position: CameraPosition, 
                                 n_frames: int) -> List[CameraPosition]:
    """
    interpolates between two camera positions
    """
    centers = np.linspace(initial_position.center, end_position.center, num=n_frames)
    angless = np.linspace(initial_position.angles, end_position.angles, num=n_frames)
    zooms = np.linspace(initial_position.zoom, end_position.zoom, num=n_frames)
    perspectives = np.linspace(initial_position.perspective, end_position.perspective, num=n_frames)
    out = [CameraPosition(
        center=center,
        angles=angles,
        zoom=zoom,
        perspective=perspective
    ) for center, angles, zoom, perspective in zip(centers, angless, zooms, perspectives)]
    return out

def interpolate_frames(view_list: List[CameraPosition], n_frames: int) -> List[CameraPosition]:
    frames: List[CameraPosition] = []
    for i, view in enumerate(view_list):
        if i == 0:
            continue
        frames.extend(interpolate_camera_positions(view_list[i-1], view, n_frames))
    return frames

def make_movie(n_frames=60, screenshot_path: Optional[Path] = None, loop=False):
    if screenshot_path is None:
        screenshot_path = Path().home() / "screenshot"
    screenshot_path.mkdir(exist_ok=True)
    if loop:
        camera_view_list.append(camera_view_list[0])
    frames = interpolate_frames(camera_view_list, n_frames)
    for i, frame in enumerate(frames):
        frame.set_on_camera(viewer.camera)
        take_screenshot(screenshot_path / f"{i:05d}.png")
    pngs_to_movie(screenshot_path)


def take_screenshot(screenshot_path: Path):
    viewer.window.screenshot(path=screenshot_path, canvas_only=True)

def append_position():
    camera_view_list.append(CameraPosition.fromViewerCamera(
        viewer.camera
    ))

def main():
    screenshot_path = Path().home() / "Documents/screenshoot"
    screenshot_path.mkdir(exist_ok=True)
    print(CameraPosition.fromViewerCamera(viewer.camera))
    # take_screenshot(screenshot_path/"1.png")

def pngs_to_movie(screenshot_path: Path):
    screenshots = sorted(screenshot_path.glob("*.png"))
    first_frame = cv2.imread(str(screenshots[0]))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    height, width, _ = first_frame.shape
    writer = cv2.VideoWriter(str(screenshot_path / "movie.mp4"), fourcc, 60, (width, height))
    for frame_path in screenshots:
        frame = cv2.imread(str(frame_path))
        writer.write(frame)
    writer.release()
    for frame_path in screenshots:
        frame_path.unlink()


    
