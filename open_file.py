from pathlib import Path

import IPython

ipython = IPython.get_ipython()

if "__IPYTHON__" in globals():
    ipython.magic("load_ext autoreload")
    ipython.magic("autoreload 2")

import napari
import tifffile
import record_movie


img = tifffile.imread(
    "/Users/petern/Documents/tmp/20230718-check_comms/"
    "elav_lexAlexaop_myr_sf_GFP-647GFP405fas2RXXelav-1-1.tif"
)

viewer = napari.view_image(img, channel_axis=1)
viewer.layers[1].scale = [4, 1, 1]
viewer.layers[0].scale = [4, 1, 1]

record_movie.camera_view_list = record_movie.load_camera_position_list(Path("tmp.json"))
