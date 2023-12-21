import numpy as np
from PyQt6 import QtWidgets
from typing import Any, Dict, Optional, Tuple, Union
from vispy import scene, color

from .base_plot_widget import BasePlotWidget
from ..visuals.bar_plot import BarPlot
from ..helpers.ranged_pan_zoom import RangedPanZoomCamera


class BarPlotWidget(BasePlotWidget):
    layout: QtWidgets.QVBoxLayout

    def __init__(self):
        super().__init__()

        self._configure_2d()
        self.view.camera = RangedPanZoomCamera(aspect=1)
        self._image = scene.visuals.Image(cmap="grays", parent=self.view.scene)
        self.link_views()
        self._configure_2d()
        hist = scene.Histogram(data, bins, color, orientation)
        self.view.add(hist)
        self.view.camera.set_range()
        return hist

    def update(
        self,
        data: np.ndarray = None,
        clim: Union[Tuple[float, float], str] = None,
        cmap: str = None,
    ):
        if type(data) == np.ndarray:
            self.check_update_viewbox(data)
            self._image.set_data(data)
        if type(clim) == tuple:
            self._image.clim = clim
            self._clim_auto = False
        elif type(clim) == str and clim == "auto":
            self._clim_auto = True
        if type(cmap) == str:
            self._image.cmap = cmap
        self.canvas.update()
        if self._clim_auto == True:
            self._image.clim = "auto"

    def check_update_viewbox(self, new_data):
        new_shape = new_data.shape[::-1]
        if self._image._data is None or self._image.size != new_shape:
            self.view.camera.set_range((0, new_shape[0]), (0, new_shape[1]))
