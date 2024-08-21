from typing import Optional
from typing import Union

import numpy as np

from vispy import color
from vispy import scene

from ..helpers.ranged_pan_zoom import RangedPanZoomCamera
from .base_plot_widget import BasePlotWidget


class ImageWidget(BasePlotWidget):
    def __init__(
        self,
        data=None,
        method="auto",
        grid=(1, 1),
        cmap="viridis",
        clim="auto",
        gamma=1.0,
        interpolation="nearest",
        texture_format=None,
        aspect=None,
        *args,
        **kwargs,
    ):
        if "cbar_cmap" not in kwargs:
            kwargs["cbar_cmap"] = cmap
        super().__init__(*args, **kwargs)

        self._configure_2d()
        camera = RangedPanZoomCamera(aspect=1)
        self.view.camera = camera
        self.visual = scene.visuals.Image(
            data,
            method,
            grid,
            cmap,
            clim,
            gamma,
            interpolation,
            texture_format,
            parent=self.view.scene,
        )
        self.link_views()
        if aspect is not None:
            camera.aspect = aspect
        self._clim_auto = True

    def update(
        self,
        data: Optional[np.ndarray] = None,
        clim: Optional[Union[tuple[float, float], str]] = None,
        cmap: Optional[Union[str, color.Colormap]] = None,
    ):
        if data is not None:
            self.check_update_viewbox(data)
            self.visual.set_data(data)

        if clim is not None:
            if isinstance(clim, tuple):
                self.visual.clim = clim
                if self.cbar is not None:
                    self.cbar.clim = clim
                self._clim_auto = False
            elif isinstance(clim, str) and clim == "auto":
                self._clim_auto = True

        if cmap is not None:
            self.visual.cmap = cmap
            if self.cbar is not None:
                self.cbar.cmap = cmap

        self.canvas.update()
        if self._clim_auto is True:
            if self.cbar is not None:
                self.cbar.clim = self.visual.clim
            self.visual.clim = "auto"

    def check_update_viewbox(self, new_data):
        new_shape = new_data.shape[::-1]
        if self.visual._data is None or self.visual.size != new_shape:
            self.view.camera.set_range((0, new_shape[0]), (0, new_shape[1]))
