import asyncio
import logging
import pickle
import signal
import socket
from collections.abc import AsyncGenerator
from dataclasses import field
from typing import Any
from typing import Optional

from qtpy import QtCore
from qtpy import QtWidgets

import ezmsg.core as ez

from ..frontends.main_window import EzWindowMeta
from ..helpers.constants import BYTEORDER
from ..helpers.constants import UINT64_SIZE
from .plot_vis import PlotVis

logger = logging.getLogger(__name__)


class SimpleApplicationSettings(ez.Settings):
    title: str
    width: int
    height: int
    external_timer: bool
    external_timer_interval: int = 33
    ui_file: Optional[str] = None


class SimpleApplicationState(ez.State):
    app: Optional[QtWidgets.QApplication]
    timer: Optional[QtCore.QTimer]
    win: Optional[QtWidgets.QMainWindow]


class SimpleApplication(ez.Unit):
    """
    Creates a pyqt application with a window + visuals
    """

    SETTINGS = SimpleApplicationSettings
    STATE = SimpleApplicationState

    visuals: list[ez.Unit]

    def initialize(self):
        self.STATE.app = None
        self.STATE.timer = None
        self.STATE.win = None

    @ez.main
    def run_visuals(self) -> None:
        # Setup signal handling for Ctrl-C
        signal.signal(signal.SIGINT, signal_handler)
        self.STATE.app = QtWidgets.QApplication([])

        # Window
        self.STATE.win = QtWidgets.QMainWindow()
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        for visual in self.visuals:
            layout.addWidget(visual.build())
        central_widget.setLayout(layout)
        self.STATE.win.setCentralWidget(central_widget)
        self.STATE.win.resize(self.SETTINGS.width, self.SETTINGS.height)
        self.STATE.win.setWindowTitle(self.SETTINGS.title)

        if self.SETTINGS.external_timer is True:
            self.STATE.timer = QtCore.QTimer()
            self.STATE.timer.setInterval(self.SETTINGS.external_timer_interval)
            self.STATE.timer.timeout.connect(self.update)
            self.STATE.timer.start()

        self.STATE.win.show()
        self.STATE.app.exec()

        if self.SETTINGS.external_timer is True and self.STATE.timer is not None:
            self.STATE.timer.stop()
        else:
            for visual in self.visuals:
                visual.STATE.timer.stop()

        self.STATE.app.quit()
        raise ez.NormalTermination

    def shutdown(self) -> None:
        if self.STATE.app is not None:
            self.STATE.app.quit()

    def update(self) -> None:
        for visual in self.visuals:
            visual.update()


class ApplicationSettings(ez.Settings):
    window: EzWindowMeta
    external_timer: bool
    external_timer_interval: int = 33
    width: int = 640
    height: int = 640
    kwargs: dict = field(default_factory=dict)


class ApplicationState(ez.State):
    app: Optional[QtWidgets.QApplication]
    timer: Optional[QtCore.QTimer]
    win: Optional[QtWidgets.QMainWindow]
    command_socket: socket.SocketType
    response_socket: socket.SocketType
    command_relay_socket: socket.SocketType
    response_relay_socket: socket.SocketType


class Application(ez.Unit):
    """
    Creates a pyqt application with a window + visuals
    """

    INPUT = ez.InputStream(Any)
    OUTPUT = ez.OutputStream(Any)

    SETTINGS = ApplicationSettings
    STATE = ApplicationState

    visuals: dict[str, PlotVis]

    def initialize(self) -> None:
        self.STATE.app = None
        self.STATE.timer = None
        self.STATE.win = None
        # Setup command relay which forwards messages into ezmsg
        self.STATE.command_socket, self.STATE.command_relay_socket = socket.socketpair()
        # Setup response relay which forwards messages to the frontend.
        (
            self.STATE.response_relay_socket,
            self.STATE.response_socket,
        ) = socket.socketpair()

    @ez.subscriber(INPUT)
    async def on_response(self, message: Any) -> None:
        raw = pickle.dumps(message)
        raw_size = len(raw).to_bytes(UINT64_SIZE, byteorder=BYTEORDER, signed=False)
        self.STATE.response_relay_socket.send(raw_size)
        self.STATE.response_relay_socket.send(raw)

    @ez.publisher(OUTPUT)
    async def on_command(self) -> AsyncGenerator:
        command_relay_reader, writer = await asyncio.open_connection(
            sock=self.STATE.command_relay_socket
        )

        try:
            while True:
                raw_size_bytes = await command_relay_reader.read(UINT64_SIZE)
                raw_size = int.from_bytes(
                    raw_size_bytes, byteorder=BYTEORDER, signed=False
                )
                raw = await command_relay_reader.read(raw_size)
                if len(raw) == 0:
                    break
                message = pickle.loads(raw)
                yield self.OUTPUT, message
        finally:
            writer.close()
            await writer.wait_closed()

    @ez.main
    def run_visuals(self) -> None:
        # Setup signal handling for Ctrl-C
        signal.signal(signal.SIGINT, signal_handler)
        self.STATE.app = QtWidgets.QApplication([])

        # Window
        self.STATE.win = self.SETTINGS.window(
            command_socket=self.STATE.command_socket,
            response_socket=self.STATE.response_socket,
            **self.SETTINGS.kwargs,
        )
        self.STATE.win.resize(self.SETTINGS.width, self.SETTINGS.height)

        # Attach visuals to widgets in MainWindow
        widgets = {}
        for name, visual in self.visuals.items():
            widgets[name] = visual.build()
        self.STATE.win.add_visual_widgets(widgets)

        if self.SETTINGS.external_timer:
            self.STATE.timer = QtCore.QTimer()
            self.STATE.timer.setInterval(self.SETTINGS.external_timer_interval)
            self.STATE.timer.timeout.connect(self.update)
            self.STATE.timer.start()

        self.STATE.win.show()
        self.STATE.app.exec()

        if self.SETTINGS.external_timer and self.STATE.timer is not None:
            self.STATE.timer.stop()
        else:
            for visual in self.visuals.values():
                visual.STATE.timer.stop()
        self.STATE.app.quit()
        raise ez.NormalTermination

    def shutdown(self) -> None:
        if self.STATE.app is not None:
            self.STATE.app.quit()
        self.STATE.command_socket.close()
        self.STATE.command_relay_socket.close()
        self.STATE.response_socket.close()
        self.STATE.response_relay_socket.close()

    def update(self) -> None:
        for visual in self.visuals.values():
            visual.update()


def signal_handler(sig, frame):
    """Handle the interrupt signal and close the application."""
    QtWidgets.QApplication.instance().quit()
