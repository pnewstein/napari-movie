"""
records a movie by interpolating between views

USAGE:
append_position(viewer)
# move camera to next position
append_position(viewer)
make_movie(viewer)
"""

from pathlib import Path
import dataclasses
from typing import Tuple, List, Optional
import json


import cv2
import napari
import numpy as np


FRAME_RATE = 60

DEFAULT_PATH = Path().home() / "screenshot"


@dataclasses.dataclass(frozen=True)
class CameraPosition:
    """
    represents a camera position
    """

    center: Tuple[float, float, float]
    angles: Tuple[float, float, float]
    zoom: float
    perspective: float
    transition_time: float

    def __eq__(self, other) -> bool:
        if type(self) != type(other):
            return False
        print("here")
        print(dataclasses.astuple(self))
        print(dataclasses.astuple(other))
        return dataclasses.astuple(self) == dataclasses.astuple(other)

    @classmethod
    def fromViewerCamera(
        cls, camera: napari.components.camera.Camera, transition_time: float
    ):
        """
        records the postiton of teh camera
        """
        return cls(
            center=camera.center,
            angles=camera.angles,
            zoom=camera.zoom,
            perspective=camera.perspective,
            transition_time=transition_time,
        )

    def set_on_camera(self, camera: napari.components.camera.Camera):
        """
        sets the recorded postiton to the current camera postiton
        """
        camera.center = self.center
        camera.angles = self.angles
        camera.zoom = self.zoom
        camera.perspective = self.perspective


camera_view_list: List[CameraPosition] = []


def load_camera_position_list(path: Path) -> List[CameraPosition]:
    """
    Loads a camara positison list from a path
    """
    json_list = json.loads(path.read_text("utf-8"))
    out: List[CameraPosition] = []
    for pos_dict in json_list:
        center0, center1, center2 = pos_dict["center"]
        angles0, angles1, angles2 = pos_dict["angles"]
        out.append(
            CameraPosition(
                center=(center0, center1, center2),
                angles=(angles0, angles1, angles2),
                zoom=pos_dict["zoom"],
                perspective=pos_dict["perspective"],
                transition_time=pos_dict["transition_time"],
            )
        )
    return out


def save_camera_position_list(camera_positions: List[CameraPosition], path: Path):
    """
    writes the list of camera positions to a json file
    """
    out = [dataclasses.asdict(pos) for pos in camera_positions]
    path.write_text(json.dumps(out, indent=2), "utf-8")


def interpolate_camera_positions(
    initial_position: CameraPosition, end_position: CameraPosition, trans_time: float
) -> List[CameraPosition]:
    """
    interpolates between two camera positions
    """
    # handle 365 issue
    ip_angles = list(initial_position.angles)
    for i, angle in enumerate(ip_angles):
        current_diff = abs(angle - end_position.angles[i])
        add_diff = abs(angle + 365 - end_position.angles[i])
        sub_diff = abs(angle - 365 - end_position.angles[i])
        if add_diff < current_diff:
            ip_angles[i] += 365
        elif sub_diff < current_diff:
            ip_angles[i] -= 365
    n_frames = round(FRAME_RATE * trans_time)
    centers = np.linspace(initial_position.center, end_position.center, num=n_frames)
    angless = np.linspace(tuple(ip_angles), end_position.angles, num=n_frames)
    zooms = np.linspace(initial_position.zoom, end_position.zoom, num=n_frames)
    # make sure angles is back into range -180, 180
    angless += (4 * 360) + 180
    angless %= 360
    angless -= 180
    perspectives = np.linspace(
        initial_position.perspective, end_position.perspective, num=n_frames
    )
    out = [
        CameraPosition(
            center=center,
            angles=angles,
            zoom=zoom,
            perspective=perspective,
            transition_time=0,
        )
        for center, angles, zoom, perspective in zip(
            centers, angless, zooms, perspectives
        )
    ]
    return out


def interpolate_frames(view_list: List[CameraPosition]) -> List[CameraPosition]:
    """
    Figures out all the frames between some frames
    """
    frames: List[CameraPosition] = []
    for i, view in enumerate(view_list):
        if i == 0:
            continue
        frames.extend(
            interpolate_camera_positions(
                view_list[i - 1], view, view.transition_time
            )
        )
    return frames


def make_movie(viewer, screenshot_path: Optional[Path] = None, loop=False, verbose=True):
    """
    makes a movie from all the appened postions
    """
    if screenshot_path is None:
        screenshot_path = DEFAULT_PATH
    screenshot_path.mkdir(exist_ok=True)
    if loop:
        camera_view_list.append(camera_view_list[0])
    frames = interpolate_frames(camera_view_list)
    for i, frame in enumerate(frames):
        frame.set_on_camera(viewer.camera)
        take_screenshot(viewer, screenshot_path / f"{i:05d}.png")
        if verbose and i % 10 == 0:
            print(f"proccesing frame {i} of {len(frames)}")
            
    pngs_to_movie(screenshot_path)


def take_screenshot(viewer, screenshot_path: Path):
    """
    takes a screenshot saves to path
    """
    viewer.window.screenshot(path=screenshot_path, canvas_only=True)


def append_position(viewer, transition_time=1, json_path=None):
    """
    appends the current position to camera_view_list
    also saves as json to path
    """
    if json_path is None:
        json_path = DEFAULT_PATH / "movie.json"
    camera_view_list.append(
        CameraPosition.fromViewerCamera(
            viewer.camera,
            transition_time=transition_time,
        )
    )


def pngs_to_movie(screenshot_path: Path, verbose=True):
    screenshots = sorted(screenshot_path.glob("*.png"))
    first_frame = cv2.imread(str(screenshots[0]))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    height, width, _ = first_frame.shape
    writer = cv2.VideoWriter(
        str(screenshot_path / "movie.mp4"), fourcc, FRAME_RATE, (width, height)
    )
    for frame_path in screenshots:
        frame = cv2.imread(str(frame_path))
        writer.write(frame)
    writer.release()
    for frame_path in screenshots:
        frame_path.unlink()
