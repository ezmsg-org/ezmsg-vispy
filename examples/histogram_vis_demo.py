import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from dataclasses import field
from itertools import cycle
from typing import Any

import numpy as np

import ezmsg.core as ez
from ezmsg.util.rate import Rate
from ezmsg.vispy.units.application import SimpleApplication
from ezmsg.vispy.units.application import SimpleApplicationSettings
from ezmsg.vispy.units.histogram_vis import HistogramVis
from ezmsg.vispy.units.histogram_vis import HistogramVisSettings


@dataclass
class HistogramMessage:
    data: np.ndarray
    bins: np.ndarray


class DataGeneratorSettings(ez.Settings):
    noise_freqs: list[float] = field(default_factory=lambda: [1.0, 50.0, 100.0])
    refresh_rate: float = 30.0
    noise_interval: float = 2.5


class DataGeneratorState(ez.State):
    noise_cycle: cycle
    current_noise_f: float
    noise_interval_ts: float


class DataGenerator(ez.Unit):
    SETTINGS = DataGeneratorSettings
    STATE = DataGeneratorState

    OUTPUT = ez.OutputStream(Any)

    def initialize(self):
        self.STATE.noise_cycle = cycle(self.SETTINGS.noise_freqs)
        self.STATE.current_noise_f = next(self.STATE.noise_cycle)
        self.STATE.noise_interval_ts = time.time()

    @ez.publisher(OUTPUT)
    async def spawn_message(self) -> AsyncGenerator:
        rate = Rate(self.SETTINGS.refresh_rate)
        while True:
            if (
                time.time() - self.STATE.noise_interval_ts
                > self.SETTINGS.noise_interval
            ):
                self.STATE.current_noise_f = next(self.STATE.noise_cycle)
                self.STATE.noise_interval_ts = time.time()
            data = (
                np.random.normal(loc=self.STATE.current_noise_f, scale=3, size=1000),
            )
            histogram, bins = np.histogram(data, bins="auto")

            yield self.OUTPUT, HistogramMessage(data=histogram, bins=bins)
            await rate.sleep()


class HistogramAppSettings(ez.Settings):
    data_attr: str
    bins_attr: str
    color: str = "w"
    orientation = "v"


class HistogramApp(ez.Collection):
    SETTINGS = HistogramAppSettings

    INPUT = ez.InputStream(Any)

    PLOT = HistogramVis()
    APP = SimpleApplication()

    def configure(self):
        self.PLOT.apply_settings(
            HistogramVisSettings(
                data_attr=self.SETTINGS.data_attr,
                bins_attr=self.SETTINGS.bins_attr,
                color=self.SETTINGS.color,
                orientation=self.SETTINGS.orientation,
                xax_en=True,
                yax_en=True,
                gridlines_en=True,
            )
        )

        self.APP.apply_settings(
            SimpleApplicationSettings(
                title="A moderately cool application",
                width=640,
                height=1000,
                external_timer=True,
                external_timer_interval=33,
            )
        )

        self.APP.visuals = [self.PLOT]

    def network(self):
        return ((self.INPUT, self.PLOT.INPUT),)


class HistogramDemo(ez.Collection):
    HISTOGRAM_PLOT = HistogramApp()
    HISTOGRAM_DATA = DataGenerator()

    def configure(self):
        self.HISTOGRAM_PLOT.apply_settings(
            HistogramAppSettings(data_attr="data", bins_attr="bins")
        )
        self.HISTOGRAM_DATA.apply_settings(DataGeneratorSettings())

    def network(self):
        return ((self.HISTOGRAM_DATA.OUTPUT, self.HISTOGRAM_PLOT.INPUT),)

    def process_components(self):
        return (
            self.HISTOGRAM_PLOT,
            self.HISTOGRAM_DATA,
        )


if __name__ == "__main__":
    system = HistogramDemo()
    ez.run(SYSTEM=system)
