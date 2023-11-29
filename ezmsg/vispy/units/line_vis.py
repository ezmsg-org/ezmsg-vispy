import ezmsg.core as ez
from ezmsg.util.messages.axisarray import AxisArray
import numpy as np
from typing import Any, Optional, Tuple, Union
from PyQt6 import QtCore

from .plot_vis import PlotVisState, PlotVisSettings, PlotVis
from ..widgets.line_widget import LineWidget


# LINE PLOT
class LineVisState(PlotVisState):
    """
    State for a Line
    data: The raw data to display
    _update: Bool to indicate if plot visual needs updating.
    """

    data: np.ndarray = None
    set_range: bool = False
    _update: bool = False


class LineVisSettings(PlotVisSettings):
    """
    Settings for a Line
    """

    data_attr: Optional[str] = None
    color: Union[Tuple, str] = (0.5, 0.5, 0.5, 1)
    width: float = 1.0


class LineVis(PlotVis):
    """
    Subscribe to a topic and visualize the data in a plot viz.
    """

    INPUT = ez.InputStream(Any)

    STATE: LineVisState
    SETTINGS: LineVisSettings

    widget_type: type = LineWidget

    remove_attrs: list = PlotVis.remove_attrs + ["data_attr"]

    @ez.subscriber(INPUT)
    async def got_message(self, message: Any) -> None:
        if self.STATE.widget is not None:
            if issubclass(type(message), AxisArray):
                axis = message.get_axis("time")
                t = np.arange(message.shape[0]) * axis.gain + axis.offset
                data = np.empty(shape=(t.shape[0], 2))
                data[:, 0] = t
                data[:, 1] = message.data
                if self.STATE.data is None:
                    self.STATE.set_range = True
                self.STATE.data = data
                self.STATE._update = True
            elif hasattr(message, self.SETTINGS.data_attr):
                # This contains plot data.
                if self.STATE.data is None:
                    self.STATE.set_range = True
                self.STATE.data = getattr(message, self.SETTINGS.data_attr)
                self.STATE._update = True

    def update(self):
        if self.STATE._update:
            self.STATE.widget.visual.set_data(
                self.STATE.data,
            )
            if self.STATE.set_range:
                self.STATE.widget.view.camera.set_range(
                    (min(self.STATE.data[:, 0]), max(self.STATE.data[:, 0])),
                    (min(self.STATE.data[:, 1]), max(self.STATE.data[:, 1])),
                )
                self.STATE.set_range = False
            self.STATE._update = False
