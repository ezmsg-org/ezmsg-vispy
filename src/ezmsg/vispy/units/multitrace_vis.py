import ezmsg.core as ez
import numpy as np
import asyncio
import threading
from dataclasses import asdict, field, dataclass
from typing import Dict, Optional, Tuple, Sequence, Union
from ezmsg.util.messages.axisarray import AxisArray

from .plot_vis import PlotVisState, PlotVisSettings, PlotVis
from ..widgets.multitrace_widget import MultiTraceData, MultiTraceMode, MultiTraceWidget

import logging

logger = logging.getLogger(__name__)


@dataclass
class MultiTraceMessage:
    data: np.ndarray
    fs: Optional[float] = None
    x_arr: Optional[np.ndarray] = None
    trace_name: str = "default"
    ch_names: Optional[Sequence[str]] = None
    units: Optional[str] = None


class MultiTraceVisState(PlotVisState):
    loop: asyncio.AbstractEventLoop
    lock: threading.Lock
    trace_map: Dict[str, Tuple[bool, MultiTraceData]] = field(default_factory=dict)
    _update: bool = False


class MultiTraceVisSettings(PlotVisSettings):
    mode: MultiTraceMode = MultiTraceMode.SET
    trace_colors: Dict[str, set] = field(default_factory=dict)
    gridlines_en: bool = True
    axis: str = "time"


class MultiTraceVis(PlotVis):
    INPUT = ez.InputStream(MultiTraceMessage)

    STATE: MultiTraceVisState
    SETTINGS: MultiTraceVisSettings

    widget_type: type = MultiTraceWidget
    remove_attrs: list = PlotVis.remove_attrs + ["axis"]

    def initialize(self):
        self.STATE.loop = asyncio.get_event_loop()
        self.STATE.lock = threading.Lock()

    @ez.subscriber(INPUT)
    async def got_message(self, message: Union[MultiTraceMessage, AxisArray]) -> None:
        if self.STATE.widget is not None:
            if type(message) is MultiTraceMessage:
                trace_name = message.trace_name
                data = message.data
                fs = message.fs
                x_arr = message.x_arr
                trace_name = message.trace_name
                ch_names = message.ch_names
                units = message.units
            elif isinstance(message, AxisArray):
                data = message.data
                fs = 1.0 / message.get_axis(self.SETTINGS.axis).gain
                x_arr = (
                    np.arange(data.shape[0]) / fs
                    + message.get_axis(self.SETTINGS.axis).offset
                )
                trace_name = message.__class__.__name__
                ch_names = None
                units = message.get_axis(1).unit

            self.STATE.lock.acquire()
            _, trace = self.STATE.trace_map.get(trace_name, [None, None])
            if (
                trace is None
                or trace.ch_names != ch_names
                or trace.fs != fs
                # or (
                #     trace.x_arr is not None and x_arr is not None and trace.x_arr.shape != x_arr.shape
                # )
            ):
                trace = MultiTraceData(data, fs, x_arr, trace_name, ch_names, units)
            else:
                if (
                    trace.data is None
                    or self.SETTINGS.mode is MultiTraceMode.SET
                    or (
                        trace.data is not None
                        and trace.data.shape[1:] != message.data.shape[1:]
                    )
                ):
                    trace.data = message.data
                else:
                    trace.data = np.concatenate((trace.data, data), axis=0)
            self.STATE.trace_map[trace_name] = (True, trace)
            self.STATE.lock.release()
            self.STATE._update = True

    def update(self):
        if self.STATE._update is True:
            with self.STATE.lock:
                for key in self.STATE.trace_map.keys():
                    update, trace = self.STATE.trace_map[key]
                    if update is True:
                        if self.SETTINGS.mode == MultiTraceMode.ROLL:
                            self.STATE.widget.roll_data(trace)
                        if self.SETTINGS.mode == MultiTraceMode.SET:
                            self.STATE.widget.set_data(trace)
                        trace.data = None
                        self.STATE.trace_map[key] = (False, trace)
                self.STATE._update = False
