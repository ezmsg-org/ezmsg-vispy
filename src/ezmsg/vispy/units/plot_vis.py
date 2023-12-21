import asyncio
import ezmsg.core as ez
from ezmsg.util.messagegate import GateMessage
from functools import partial
from typing import Any, Optional, List
from PyQt6 import QtCore, QtWidgets
from dataclasses import asdict, field

from ..helpers.constants import TIMER_INTERVAL


class PlotVisSettings(ez.Settings):
    title: Optional[str] = None
    xax_en: bool = False
    yax_en: bool = False
    xax_pos: str = "bottom"
    yax_pos: str = "left"
    xax_type: str = "vispy"
    yax_type: str = "vispy"
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    xlabel_pos: str = "bottom"
    ylabel_pos: str = "left"
    gridlines_en: bool = False
    fg_color: str = "w"
    bg_color: str = "k"
    external_timer: bool = False


class PlotVisState(ez.State):
    widget: Optional[QtWidgets.QWidget] = None
    timer: Optional[QtCore.QTimer] = None
    evs: asyncio.Queue = field(default_factory=asyncio.Queue)


class PlotVis(ez.Unit):
    SETTINGS: PlotVisSettings
    STATE: PlotVisState

    EVS_OUTPUT = ez.OutputStream(Any)

    widget_type: type
    remove_attrs: List[str] = ["external_timer"]

    def build(self) -> QtWidgets.QWidget:
        kwargs = asdict(self.SETTINGS)
        [kwargs.pop(key) for key in self.remove_attrs]
        self.STATE.widget = self.widget_type(**kwargs)

        if not self.SETTINGS.external_timer:
            self.STATE.timer = QtCore.QTimer()
            self.STATE.timer.setInterval(TIMER_INTERVAL)
            self.STATE.timer.start()
            self.STATE.timer.timeout.connect(self.update)

        self.STATE.widget.visibility_change_ev.connect(self.set_visibility)

        return self.STATE.widget

    def stop(self) -> None:
        if not self.SETTINGS.external_timer and self.STATE.timer is not None:
            self.STATE.timer.stop()

    def set_visibility(self, visible: bool):
        # loop = asyncio.get_event_loop()
        # loop.call_soon_threadsafe(self.STATE.evs.put_nowait, visible)
        # asyncio.run_coroutine_threadsafe(self.STATE.evs.put(visible), loop)
        self.STATE.evs.put_nowait(visible)

    def update(self) -> None:
        raise NotImplementedError

    @ez.publisher(EVS_OUTPUT)
    async def on_event(self):
        while True:
            visibility = await self.STATE.evs.get()
            yield self.EVS_OUTPUT, GateMessage(visibility)
