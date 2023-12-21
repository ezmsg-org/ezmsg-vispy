import ezmsg.core as ez
import numpy as np
import time
import asyncio
import threading
from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple, Union, List
from PyQt6 import QtCore

from .plot_vis import PlotVisState, PlotVisSettings, PlotVis
from ..widgets.multi_line_widget import MultiLineWidget

import logging

logger = logging.getLogger(__name__)


class MultiLineVisState(PlotVisState):
    """
    State for a Line
    data: The raw data to display
    _update: Bool to indicate if plot visual needs updating.
    """

    data: np.ndarray = None
    fs: float = None
    loop: asyncio.BaseEventLoop = None
    lock: threading.Lock = None
    _update: bool = False
    _configured: bool = False
    ch_mins: List[float] = None
    ch_maxs: List[float] = None


class MultiLineVisSettings(PlotVisSettings):
    """
    Settings for a Line
    """

    data_attr: str = None
    fs_attr: str = None
    color: Union[Tuple, str] = (0.5, 0.5, 0.5, 1)
    width: float = 1.0
    window_length: float = 30.0  # in seconds
    channel_offset: float = 10.0
    ch_min_attr: str = None
    ch_max_attr: str = None


class MultiLineVis(PlotVis):
    INPUT = ez.InputStream(Any)

    STATE: MultiLineVisState
    SETTINGS: MultiLineVisSettings

    widget_type: type = MultiLineWidget

    remove_attrs: list = PlotVis.remove_attrs + [
        "data_attr",
        "fs_attr",
        "window_length",
        "channel_offset",
        "ch_min_attr",
        "ch_max_attr",
    ]

    def initialize(self):
        self.STATE.loop = asyncio.get_event_loop()
        self.STATE.lock = threading.Lock()

    @ez.subscriber(INPUT)
    async def got_message(self, message: Any) -> None:
        if self.STATE.widget is not None:
            if hasattr(message, self.SETTINGS.data_attr):
                if self.STATE.fs is None and hasattr(message, self.SETTINGS.fs_attr):
                    self.STATE.fs = getattr(message, self.SETTINGS.fs_attr)
                if (
                    self.SETTINGS.ch_min_attr is not None
                    and hasattr(message, self.SETTINGS.ch_min_attr) is True
                ):
                    self.STATE.ch_mins = getattr(message, self.SETTINGS.ch_min_attr)
                if (
                    self.SETTINGS.ch_max_attr is not None
                    and hasattr(message, self.SETTINGS.ch_max_attr) is True
                ):
                    self.STATE.ch_maxs = getattr(message, self.SETTINGS.ch_max_attr)
                # This contains plot data.
                new_data = getattr(message, self.SETTINGS.data_attr)
                # await self.STATE.loop.run_in_executor(None, self.STATE.lock.acquire)
                self.STATE.lock.acquire()
                if self.STATE.data is None:
                    self.STATE.data = new_data
                else:
                    self.STATE.data = np.concatenate(
                        (self.STATE.data, new_data), axis=1
                    )
                # await self.STATE.loop.run_in_executor(None, self.STATE.lock.release)
                self.STATE.lock.release()
                self.STATE._update = True
            else:
                logger.warn(f"Received message did not have data attr!")

    def update(self):
        if self.STATE._update is True:
            with self.STATE.lock:
                fs = self.STATE.fs
                try:
                    data = self.STATE.data.copy()
                except AttributeError:
                    return
                self.STATE.data = None
            if self.STATE._configured is False:
                self.STATE.widget.configure_segments(
                    window_length=self.SETTINGS.window_length,
                    channel_offset=self.SETTINGS.channel_offset,
                    fs=fs,
                    num_segments=data.shape[0],
                )
                self.STATE._configured = True
            if self.STATE.ch_mins is not None and self.STATE.ch_maxs is not None:
                self.STATE.widget.roll_data(
                    data, self.STATE.ch_mins, self.STATE.ch_maxs
                )
            else:
                self.STATE.widget.roll_data(
                    data,
                )

            self.STATE._update = False
