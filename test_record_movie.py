"""
use pytest to test the module
"""

from pathlib import Path

import record_movie


def test_serial_desearial():
    pos_list = [
        record_movie.CameraPosition((0, 0, 0), (-179, -91, -1), 0, 0, 0),
        record_movie.CameraPosition((1, 1, 1), (179, 91, 1), 1, 1, 1),
    ]
    record_movie.save_camera_position_list(pos_list, Path("tmp.json"))
    pos_list2 = record_movie.load_camera_position_list(Path("tmp.json"))
    print(pos_list)
    print(pos_list2)
    print(pos_list[1] == pos_list2[1])
    # assert all(a == b for a, b in zip(pos_list2, pos_list))

def test_interpolate():
    pos_list = [
        record_movie.CameraPosition((0, 0, 0), (-179, -91, -1), 0, 0, 0),
        record_movie.CameraPosition((1, 1, 1), (179, 91, 1), 1, 1, .1),
    ]
    interpolated = record_movie.interpolate_frames(pos_list)

    print([i.angles for i in interpolated])
    

if __name__ == "__main__":
    test_interpolate()

