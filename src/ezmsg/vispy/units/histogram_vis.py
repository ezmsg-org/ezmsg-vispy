from dataclasses import dataclass
from typing import Any
from typing import Optional

import numpy as np

import ezmsg.core as ez
from ezmsg.util.messages.axisarray import AxisArray

from ..widgets.histogram_widget import HistogramWidget
from .plot_vis import PlotVis
from .plot_vis import PlotVisSettings
from .plot_vis import PlotVisState


@dataclass
class HistogramMessage:
    data: np.ndarray
    bins: np.ndarray


class HistogramVisSettings(PlotVisSettings):
    data_attr: Optional[str] = None
    bins_attr: Optional[str] = None
    color: str = "w"
    orientation: str = "h"


class HistogramVisState(PlotVisState):
    data: np.ndarray = np.array([])
    bins: Optional[int] = None
    _update: bool = False


class HistogramVis(PlotVis):
    INPUT = ez.InputStream(Any)

    STATE = HistogramVisState
    SETTINGS = HistogramVisSettings

    widget_type: type = HistogramWidget

    remove_attrs: list[str] = PlotVis.remove_attrs + ["data_attr", "bins_attr"]

    @ez.subscriber(INPUT)
    async def got_message(self, message: Any) -> None:
        if self.STATE.widget is not None:
            if type(message) is AxisArray and "bins" in message.dims:
                self.STATE.data = message.data
                self.STATE.bins = compute_bins_from_axis(message)
                self.STATE._update = True
            elif (
                self.SETTINGS.data_attr is not None
                and self.SETTINGS.bins_attr is not None
                and hasattr(message, self.SETTINGS.data_attr)
                and hasattr(message, self.SETTINGS.bins_attr)
            ):
                self.STATE.data = getattr(message, self.SETTINGS.data_attr)
                self.STATE.bins = getattr(message, self.SETTINGS.bins_attr)
                self.STATE._update = True

    def update(self):
        if self.STATE._update:
            self.STATE.widget.update(self.STATE.data, self.STATE.bins)
            self.STATE._update = False


def compute_bins_from_axis(axis_arr):
    num_bins = axis_arr.shape[0]
    bin_spacing = axis_arr.get_axis("bins").gain
    bin_offset = axis_arr.get_axis("bins").offset
    bin_max = bin_offset + bin_spacing * num_bins
    return np.linspace(bin_offset, bin_max, num_bins + 1)
