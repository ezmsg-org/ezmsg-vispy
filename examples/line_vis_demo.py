import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import numpy as np
from frontends.line_vis_frontend import LineVisFrontend
from frontends.line_vis_frontend import WaveformCfgMessage

# Module specific imports
import ezmsg.core as ez
from ezmsg.util.rate import Rate
from ezmsg.vispy.units.application import Application
from ezmsg.vispy.units.application import ApplicationSettings
from ezmsg.vispy.units.line_vis import LineVis
from ezmsg.vispy.units.line_vis import LineVisSettings

logger = logging.getLogger(__name__)


def sawtooth(fsig, t):
    fs = 1.0 / np.mean(np.diff(t))
    tsig = 1.0 / fsig
    duration = t.shape[0] / fs
    periods_in_duration = int(np.ceil(duration / tsig))
    samples_per_period = int(np.ceil(tsig * fs))
    sawtooth_period = np.linspace(1.0, -1.0, samples_per_period)
    tiled_sawtooth = np.tile(sawtooth_period, periods_in_duration)
    samples_in_duration = int(np.ceil(duration * fs))
    waveform = tiled_sawtooth[:samples_in_duration]
    return waveform


@dataclass
class WaveformMessage:
    data: np.ndarray


class WaveformSettings(ez.Settings):
    fs: float = 1000.0  # sampling rate
    fsig: float = 1.0  # signal frequency
    waveform_type: str = "sine"
    refresh_rate: float = 60.0
    window_length: float = 5.0  # in seconds


class WaveformState(ez.State):
    fsig: float
    waveform_type: str
    t: np.ndarray
    y: np.ndarray
    freqs: np.ndarray
    fft_vals: np.ndarray
    run_lock: asyncio.Lock


class WaveformGenerator(ez.Unit):
    SETTINGS = WaveformSettings
    STATE = WaveformState

    CFG_COMMAND = ez.InputStream(WaveformCfgMessage)
    CFG_RESPONSE = ez.OutputStream(WaveformCfgMessage)

    TS_OUTPUT = ez.OutputStream(WaveformMessage)
    FS_OUTPUT = ez.OutputStream(WaveformMessage)

    def initialize(self) -> None:
        self.STATE.fsig = self.SETTINGS.fsig
        self.STATE.waveform_type = self.SETTINGS.waveform_type
        self.STATE.t = np.linspace(
            start=0,
            stop=self.SETTINGS.window_length,
            num=int(self.SETTINGS.window_length * self.SETTINGS.fs),
        )
        self.update_waveform()
        self.STATE.run_lock = asyncio.Lock()

    @ez.publisher(FS_OUTPUT)
    @ez.publisher(TS_OUTPUT)
    async def send_data_once(self) -> AsyncGenerator:
        await self.STATE.run_lock.acquire()
        freqs = self.update_waveform()
        await asyncio.sleep(1.0)
        yield self.FS_OUTPUT, WaveformMessage(freqs)
        data = np.empty(shape=(len(self.STATE.t), 2))
        data[:, 0] = self.STATE.t
        data[:, 1] = self.STATE.y
        yield self.TS_OUTPUT, WaveformMessage(data)

    @ez.subscriber(CFG_COMMAND)
    @ez.publisher(CFG_RESPONSE)
    @ez.publisher(FS_OUTPUT)
    async def on_cfg_change(self, message: WaveformCfgMessage) -> AsyncGenerator:
        self.STATE.waveform_type = message.waveform_type
        self.STATE.fsig = message.frequency
        freqs = self.update_waveform()
        yield self.CFG_RESPONSE, message
        if message.start:
            if self.STATE.run_lock.locked():
                self.STATE.run_lock.release()
            yield self.FS_OUTPUT, WaveformMessage(freqs)
        else:
            if not self.STATE.run_lock.locked():
                await self.STATE.run_lock.acquire()

    @ez.publisher(TS_OUTPUT)
    async def spawn_message(self) -> AsyncGenerator:
        roll_sz = int(self.SETTINGS.fs / self.SETTINGS.refresh_rate)
        rate = Rate(self.SETTINGS.refresh_rate)
        data = np.empty(shape=(len(self.STATE.t), 2))
        data[:, 0] = self.STATE.t
        ctr = 0
        while True:
            if not self.STATE.run_lock.locked():
                data[:, 1] = np.roll(self.STATE.y, ctr * roll_sz)
                yield self.TS_OUTPUT, WaveformMessage(data=data)
                ctr += 1
            await rate.sleep()

    def update_waveform(self):
        if self.STATE.waveform_type == "sine":
            self.STATE.y = np.sin(2 * np.pi * self.STATE.fsig * self.STATE.t)
        elif self.STATE.waveform_type == "sawtooth":
            self.STATE.y = sawtooth(self.STATE.fsig, self.STATE.t)
        self.STATE.fft_vals = np.fft.fftshift(np.fft.fft(self.STATE.y))
        self.STATE.freqs = (
            np.fft.fftshift(np.fft.fftfreq(self.STATE.y.size)) * self.SETTINGS.fs
        )
        data = np.empty(shape=(len(self.STATE.fft_vals), 2))
        data[:, 0] = self.STATE.freqs
        data[:, 1] = np.abs(self.STATE.fft_vals)
        return data


# This is a simple example of how we use the application class
class LineApp(ez.Collection):
    # Streams for plots
    TS_INPUT = ez.InputStream(Any)  # Time series input
    FS_INPUT = ez.InputStream(Any)  # Frequency spectrum input
    # Streams for application interface
    APP_INPUT = ez.InputStream(Any)
    APP_OUTPUT = ez.OutputStream(Any)

    # Application
    APP = Application()

    # Plot units
    TIMESERIES = LineVis()
    FREQSPECTRUM = LineVis()

    def configure(self) -> None:
        # Configure plots
        self.TIMESERIES.apply_settings(
            LineVisSettings(
                data_attr="data",
                external_timer=True,
                xax_en=True,
                xlabel="Time (in seconds)",
                yax_en=True,
                ylabel="Amplitude",
                gridlines_en=True,
                title="Time Series Plot",
                color="r",
            )
        )
        self.FREQSPECTRUM.apply_settings(
            LineVisSettings(
                data_attr="data",
                external_timer=True,
                xax_en=True,
                xlabel="Frequency (in Hz)",
                yax_en=True,
                ylabel="Magnitude",
                gridlines_en=True,
                title="Frequency Spectrum Plot",
                color="y",
            )
        )
        self.APP.apply_settings(
            ApplicationSettings(
                window=LineVisFrontend,
                width=640,
                height=1000,
                external_timer=True,
                external_timer_interval=33,
            )
        )

        self.APP.visuals = {
            "ez_ts_plot": self.TIMESERIES,
            "ez_fs_plot": self.FREQSPECTRUM,
        }

    def network(self) -> ez.NetworkDefinition:
        return (
            (self.TS_INPUT, self.TIMESERIES.INPUT),
            (self.FS_INPUT, self.FREQSPECTRUM.INPUT),
            (self.APP_INPUT, self.APP.INPUT),
            (self.APP.OUTPUT, self.APP_OUTPUT),
        )


class LineVisDemo(ez.Collection):
    WAVEFORM_GENERATOR = WaveformGenerator()

    LINE_APP = LineApp()

    def configure(self) -> None:
        self.WAVEFORM_GENERATOR.apply_settings(WaveformSettings())

    # Define Connections
    def network(self) -> ez.NetworkDefinition:
        return (
            (self.WAVEFORM_GENERATOR.TS_OUTPUT, self.LINE_APP.TS_INPUT),
            (self.WAVEFORM_GENERATOR.FS_OUTPUT, self.LINE_APP.FS_INPUT),
            (self.WAVEFORM_GENERATOR.CFG_RESPONSE, self.LINE_APP.APP_INPUT),
            (self.LINE_APP.APP_OUTPUT, self.WAVEFORM_GENERATOR.CFG_COMMAND),
        )

    def process_components(self):
        return (self.LINE_APP, self.WAVEFORM_GENERATOR)


if __name__ == "__main__":
    system = LineVisDemo()
    ez.run(SYSTEM=system)
