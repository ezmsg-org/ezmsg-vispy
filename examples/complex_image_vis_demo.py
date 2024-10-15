from collections.abc import AsyncGenerator
from dataclasses import dataclass

import numpy as np

# Module specific imports
import ezmsg.core as ez
from ezmsg.util.rate import Rate
from ezmsg.vispy.units.application import SimpleApplication
from ezmsg.vispy.units.application import SimpleApplicationSettings
from ezmsg.vispy.units.complex_image_vis import ComplexImageVis
from ezmsg.vispy.units.complex_image_vis import ComplexImageVisSettings


@dataclass
class ComplexImageMessage:
    data: np.ndarray


# MESSAGE GENERATOR
class ComplexImageSettings(ez.Settings):
    fs: float  # sampling rate


class ComplexImageState(ez.State):
    running: bool = True
    image: np.ndarray = np.array([])


class ComplexImageGenerator(ez.Unit):
    SETTINGS = ComplexImageSettings
    STATE = ComplexImageState

    OUTPUT = ez.OutputStream(ComplexImageMessage)

    def initialize(self):
        self.STATE.image = complex_ramp()

    @ez.publisher(OUTPUT)
    async def spawn_message(self) -> AsyncGenerator:
        rate = Rate(self.SETTINGS.fs)
        while self.STATE.running:
            # self.STATE.image = self.STATE.image * np.random.rand(
            #     *self.STATE.image.shape
            # )
            yield self.OUTPUT, ComplexImageMessage(self.STATE.image)
            await rate.sleep()


# This is a simple example of how we use the application class
class ComplexImageApp(ez.Collection):
    # Messages
    INPUT = ez.InputStream(ComplexImageMessage)

    # SimpleApplication
    APP = SimpleApplication()

    # Plots
    IMAGE_PLOT = ComplexImageVis()

    def configure(self) -> None:
        # Configure plots
        self.IMAGE_PLOT.apply_settings(
            ComplexImageVisSettings(
                data_attr="data",
                clim="auto",
                cmap="viridis",
                external_timer=True,
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

        self.APP.visuals = [self.IMAGE_PLOT]

    # Connect the Generator outputs to the Plot inputs
    def network(self) -> ez.NetworkDefinition:
        return ((self.INPUT, self.IMAGE_PLOT.INPUT),)


class ComplexImageVisDemo(ez.Collection):
    IMAGE_GENERATOR = ComplexImageGenerator()

    IMAGE_APP = ComplexImageApp()

    def configure(self) -> None:
        self.IMAGE_GENERATOR.apply_settings(
            ComplexImageSettings(
                fs=1e2,
            )
        )

    # Define Connections
    def network(self) -> ez.NetworkDefinition:
        return ((self.IMAGE_GENERATOR.OUTPUT, self.IMAGE_APP.INPUT),)

    def process_components(self):
        return (self.IMAGE_APP, self.IMAGE_GENERATOR)


def complex_ramp(size=512, phase_range=(-np.pi, np.pi), mag_range=(0, 10)):
    """Returns a complex array where X ramps phase and Y ramps magnitude."""
    p0, p1 = phase_range
    phase_ramp = np.linspace(p0, p1 - 1 / size, size)
    m0, m1 = mag_range
    mag_ramp = np.linspace(m1, m0 + 1 / size, size)
    phase_ramp, mag_ramp = np.meshgrid(phase_ramp, mag_ramp)
    return (mag_ramp * np.exp(1j * phase_ramp)).astype(np.complex64)


if __name__ == "__main__":
    system = ComplexImageVisDemo()
    ez.run(SYSTEM=system)
