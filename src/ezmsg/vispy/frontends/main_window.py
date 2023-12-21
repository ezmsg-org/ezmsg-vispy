import logging
import pickle
import select
import qdarkstyle
from contextlib import contextmanager
from PyQt6 import QtCore, QtWidgets
from qdarkstyle.dark.palette import DarkPalette
from qdarkstyle.light.palette import LightPalette
from typing import Dict, Tuple, Union, Callable

from ..helpers.constants import UINT64_SIZE, BYTEORDER

# Silence logging for qdarkstyle package.
logging.getLogger("qdarkstyle").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

PYQT_SLOT = Union[Callable[..., None], QtCore.pyqtBoundSignal]


def merge(a, b, path=None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key] = a[key] + b[key]
            else:
                raise Exception("Conflict at %s" % ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def register_command(func) -> Callable:
    def wrapper(self):
        res = func(self)
        self.command_signal.emit(res)

    return wrapper


def register_response(msg_type):
    def _register(func):
        registrations = {msg_type: [func]}
        setattr(func, "callbacks", registrations)
        return func

    return _register


class EzWindowMeta(type(QtWidgets.QMainWindow)):
    def __init__(
        self,
        name,
        bases,
        fields,
    ):
        super().__init__(name, bases, fields)

        self.__callbacks__ = {}
        for field_value in fields.values():
            if callable(field_value):
                if hasattr(field_value, "callbacks"):
                    state = self.__callbacks__
                    self.__callbacks__ = merge(state, field_value.callbacks)

    def __call__(self, *args, **kwargs):
        obj = super().__call__(*args, **kwargs)
        return obj


class EzMainWindow(QtWidgets.QMainWindow, metaclass=EzWindowMeta):
    command_signal = QtCore.pyqtSignal(object)

    def __init__(self, command_socket, response_socket):
        super().__init__()
        self._callbacks = {
            msg_type: [(self, methods)]
            for msg_type, methods in self.__class__.__callbacks__.items()
        }
        self.set_dark_theme()

        # The command socket will send messages from ui to ezmsg.
        self.command_socket = command_socket
        # The response socket will receive messages from ezmsg to update ui.
        self.response_socket = response_socket
        # Enable a callback to activate when a response is obtained in the 0MQ subscriber.
        self.response_notification = QtCore.QSocketNotifier(
            self.response_socket.fileno(), QtCore.QSocketNotifier.Type.Read, self
        )
        self.response_notification.activated.connect(self._on_response)

        self.command_signal.connect(self._on_command)

    def set_dark_theme(self):
        self.setStyleSheet(
            qdarkstyle.load_stylesheet(qt_api="pyqt6", palette=DarkPalette)
        )

    def set_light_theme(self):
        self.setStyleSheet(
            qdarkstyle.load_stylesheet(qt_api="pyqt6", palette=LightPalette)
        )

    def add_callbacks(self, obj):
        for attr_name in dir(obj):
            field_value = getattr(obj, attr_name)
            if callable(field_value) and hasattr(field_value, "callbacks"):
                new_state = {
                    msg_type: [(obj, methods)]
                    for msg_type, methods in field_value.callbacks.items()
                }
                for msg_type in new_state:
                    if msg_type in self._callbacks:
                        self._callbacks[msg_type] = (
                            self._callbacks[msg_type] + new_state[msg_type]
                        )
                    else:
                        self._callbacks[msg_type] = new_state[msg_type]

    def set_command_signal(self, obj):
        obj.command_signal = self.command_signal

    def connect_plot_controls(self, obj):
        self.set_command_signal(obj)
        self.add_callbacks(obj)

    @QtCore.pyqtSlot()
    def _on_response(self):
        self.response_notification.setEnabled(False)
        while True:
            read_socks, _, _ = select.select([self.response_socket], [], [], 0)
            if len(read_socks) <= 0:
                break
            for sock in read_socks:
                raw_size_bytes = sock.recv(UINT64_SIZE)
                raw_size = int.from_bytes(
                    raw_size_bytes, byteorder=BYTEORDER, signed=False
                )
                raw = sock.recv(raw_size)
                msg = pickle.loads(raw)
                for registry in self._callbacks.get(type(msg), list()):
                    obj, callbacks = registry
                    for callback in callbacks:
                        if callable(callback):
                            callback(obj, msg)
        self.response_notification.setEnabled(True)

    @QtCore.pyqtSlot(object)
    def _on_command(self, msg):
        raw = pickle.dumps(msg)
        raw_size = len(raw).to_bytes(UINT64_SIZE, byteorder=BYTEORDER, signed=False)
        self.command_socket.send(raw_size)
        self.command_socket.send(raw)
        for registry in self._callbacks.get(type(msg), list()):
            obj, callbacks = registry
            for callback in callbacks:
                if callable(callback):
                    callback(obj, msg)

    def add_visual_widgets(self, visuals: Dict[str, QtWidgets.QWidget]):
        # Attach visuals to widgets in MainWindow
        for ui_name, visual_widget in visuals.items():
            try:
                widget = getattr(self, ui_name)
                widget.setLayout(visual_widget.layout())
                self.connect_plot_controls(visual_widget)
            except AttributeError as err:
                logger.error(err)

    def closeEvent(self, event):
        self.response_notification.setEnabled(False)
        self.command_socket.close()
        self.response_socket.close()
        event.accept()
