from typing import Any
from typing import Optional
from typing import Union

import numpy as np

import ezmsg.core as ez

from ..widgets.image_widget import ImageWidget
from .plot_vis import PlotVis
from .plot_vis import PlotVisSettings
from .plot_vis import PlotVisState


class ImageVisState(PlotVisState):
    data: np.ndarray = None
    clim: Optional[Union[tuple[float, float], str]] = "auto"
    cmap: Optional[str] = "grays"
    _update: bool = False


class ImageVisSettings(PlotVisSettings):
    data_attr: str = None
    clim: Union[tuple[float, float], str] = "auto"
    cmap: str = "grays"
    aspect: float = None


class ImageVis(PlotVis):
    INPUT = ez.InputStream(Any)

    STATE = ImageVisState
    SETTINGS = ImageVisSettings

    widget_type: type = ImageWidget

    remove_attrs: list = PlotVis.remove_attrs + ["data_attr"]

    def initialize(self):
        self.STATE.clim = self.SETTINGS.clim
        self.STATE.cmap = self.SETTINGS.cmap

    @ez.subscriber(INPUT)
    async def got_message(self, message: Any) -> None:
        if self.STATE.widget is not None:
            if hasattr(message, self.SETTINGS.data_attr):
                self.STATE.data = getattr(message, self.SETTINGS.data_attr)
                self.STATE._update = True

    def update(self):
        if self.STATE._update:
            self.STATE.widget.update(
                data=self.STATE.data, clim=self.STATE.clim, cmap=self.STATE.cmap
            )
            self.STATE._update = False
