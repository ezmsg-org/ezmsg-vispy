import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import field
from typing import Any

import numpy as np

# Module specific imports
import ezmsg.core as ez
from ezmsg.util.rate import Rate
from ezmsg.vispy.units.application import SimpleApplication
from ezmsg.vispy.units.application import SimpleApplicationSettings
from ezmsg.vispy.units.multitrace_vis import MultiTraceMessage
from ezmsg.vispy.units.multitrace_vis import MultiTraceVis
from ezmsg.vispy.units.multitrace_vis import MultiTraceVisSettings
from ezmsg.vispy.widgets.multitrace_widget import MultiTraceMode

logger = logging.getLogger(__name__)


# MESSAGE GENERATOR
class MultiWaveformSettings(ez.Settings):
    fs: float = 300.0  # sampling rate
    fsig: list[float] = field(
        default_factory=lambda: [1.0, 5.0, 10.0]
    )  # signal frequency
    refresh_rate: float = 60.0
    window_length: float = 1.0  # in seconds
    trace_name: str = "default"


class MultiWaveformState(ez.State):
    fsig: list[float] = None
    t: np.ndarray = None
    y: np.ndarray = None


class MultiWaveformGenerator(ez.Unit):
    SETTINGS = MultiWaveformSettings
    STATE = MultiWaveformState

    TS_OUTPUT = ez.OutputStream(MultiTraceMessage)

    def initialize(self) -> None:
        self.STATE.fsig = np.array(self.SETTINGS.fsig)
        self.STATE.t = np.linspace(
            start=0,
            stop=self.SETTINGS.window_length,
            num=int(self.SETTINGS.window_length * self.SETTINGS.fs),
        )
        self.update_waveform()

    @ez.publisher(TS_OUTPUT)
    async def spawn_message(self) -> AsyncGenerator:
        rate = Rate(self.SETTINGS.fs)
        while True:
            sample = np.sin(2 * np.pi * self.STATE.fsig * time.time())[:, np.newaxis]

            yield (
                self.TS_OUTPUT,
                MultiTraceMessage(
                    fs=self.SETTINGS.fs,
                    data=sample.T,
                    trace_name=self.SETTINGS.trace_name,
                ),
            )
            await rate.sleep()

    def update_waveform(self):
        self.STATE.y = np.empty(
            shape=(
                len(self.SETTINGS.fsig),
                len(self.STATE.t),
            )
        )
        for idx, f in enumerate(self.SETTINGS.fsig):
            self.STATE.y[idx] = np.sin(2 * np.pi * f * self.STATE.t)


# This is a simple example of how we use the application class
class MultiTraceApp(ez.Collection):
    # Messages
    INPUT = ez.InputStream(Any)

    # SimpleApplication
    APP = SimpleApplication()

    # Plots
    MULTI_PLOT = MultiTraceVis()

    def configure(self) -> None:
        # Configure plots
        self.MULTI_PLOT.apply_settings(
            MultiTraceVisSettings(
                mode=MultiTraceMode.ROLL,
                external_timer=True,
                xax_en=True,
            )
        )

        # Configure application
        # By enabling external_timer we ensure that the plots are updated
        # in sync
        self.APP.apply_settings(
            SimpleApplicationSettings(
                title="A moderately cool application",
                width=640,
                height=1000,
                external_timer=True,
                external_timer_interval=33,
            )
        )

        self.APP.visuals = [self.MULTI_PLOT]

    # Connect the Generator outputs to the Plot inputs
    def network(self) -> ez.NetworkDefinition:
        return ((self.INPUT, self.MULTI_PLOT.INPUT),)


class MultiTraceVisDemo(ez.Collection):
    MULTI_GENERATOR = MultiWaveformGenerator()
    MULTI_GENERATOR2 = MultiWaveformGenerator()

    MULTI_APP = MultiTraceApp()

    def configure(self) -> None:
        self.MULTI_GENERATOR.apply_settings(
            MultiWaveformSettings(trace_name="source 1")
        )
        self.MULTI_GENERATOR2.apply_settings(
            MultiWaveformSettings(trace_name="source 2")
        )

    # Define Connections
    def network(self) -> ez.NetworkDefinition:
        return (
            (self.MULTI_GENERATOR.TS_OUTPUT, self.MULTI_APP.INPUT),
            (self.MULTI_GENERATOR2.TS_OUTPUT, self.MULTI_APP.INPUT),
        )

    def process_components(self):
        return (self.MULTI_APP, self.MULTI_GENERATOR)


if __name__ == "__main__":
    system = MultiTraceVisDemo()
    ez.run(system)
