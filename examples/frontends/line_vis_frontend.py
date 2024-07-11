import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from qtpy import QtGui
from qtpy import QtWidgets

from ezmsg.vispy.frontends.main_window import EzMainWindow
from ezmsg.vispy.frontends.main_window import register_command
from ezmsg.vispy.frontends.main_window import register_response

sys.path.append(str(Path(__file__).parent))
from ui_line_vis_frontend import Ui_AppWindow

logger = logging.getLogger(__name__)


@dataclass
class WaveformCfgMessage:
    waveform_type: str
    frequency: float
    start: bool


class LineVisFrontend(EzMainWindow, Ui_AppWindow):
    ez_frequency_dial: QtWidgets.QDial
    ez_waveform_type: QtWidgets.QComboBox
    ez_start_btn: QtWidgets.QPushButton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.ez_waveform_type.addItem(QtGui.QIcon("resources/sine.png"), "sine")
        self.ez_waveform_type.addItem(QtGui.QIcon("resources/triangle.png"), "sawtooth")

        self.ez_frequency_dial.setMinimum(1)
        self.ez_frequency_dial.setMaximum(100)

        self.started = False

        self.ez_frequency_dial.valueChanged.connect(self.preprocess_waveform_cfg)
        self.ez_waveform_type.currentIndexChanged.connect(self.on_waveform_type_change)
        self.ez_waveform_type.currentIndexChanged.connect(self.preprocess_waveform_cfg)
        self.ez_start_btn.clicked.connect(self.on_start_btn)
        self.ez_start_btn.clicked.connect(self.preprocess_waveform_cfg)

    @register_command
    def preprocess_waveform_cfg(self):
        frequency = self.ez_frequency_dial.value()
        waveform_type = self.ez_waveform_type.currentText()
        return WaveformCfgMessage(
            frequency=frequency, waveform_type=waveform_type, start=self.started
        )

    @register_response(WaveformCfgMessage)
    def set_wavefrom_cfg(self, msg):
        print(f"Received waveform config: {msg}")

    def on_start_btn(self):
        self.started = not self.started
        self.ez_start_btn.setText("Stop" if self.started else "Start")

    def on_waveform_type_change(self):
        print(f"Waveform type changed: {self.ez_waveform_type.currentText()}")
