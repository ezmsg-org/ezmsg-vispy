from collections.abc import AsyncGenerator
from dataclasses import dataclass

import numpy as np

# Module specific imports
import ezmsg.core as ez
from ezmsg.util.rate import Rate
from ezmsg.vispy.units.application import SimpleApplication
from ezmsg.vispy.units.application import SimpleApplicationSettings
from ezmsg.vispy.units.image_vis import ImageVis
from ezmsg.vispy.units.image_vis import ImageVisSettings


@dataclass
class ImageMessage:
    data: np.ndarray


# MESSAGE GENERATOR
class ImageSettings(ez.Settings):
    fs: float  # sampling rate


class ImageState(ez.State):
    running: bool = True


class ImageGenerator(ez.Unit):
    SETTINGS = ImageSettings
    STATE = ImageState

    OUTPUT = ez.OutputStream(ImageMessage)

    @ez.publisher(OUTPUT)
    async def spawn_message(self) -> AsyncGenerator:
        rate = Rate(self.SETTINGS.fs)
        while self.STATE.running:
            yield self.OUTPUT, ImageMessage(data=get_image())
            await rate.sleep()


# This is a simple example of how we use the application class
class ImageApp(ez.Collection):
    # Messages
    INPUT = ez.InputStream(ImageMessage)

    # SimpleApplication
    APP = SimpleApplication()

    # Plots
    IMAGE_PLOT = ImageVis()

    def configure(self) -> None:
        # Configure plots
        self.IMAGE_PLOT.apply_settings(
            ImageVisSettings(
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


class ImageVisDemo(ez.Collection):
    IMAGE_GENERATOR = ImageGenerator()

    IMAGE_APP = ImageApp()

    def configure(self) -> None:
        self.IMAGE_GENERATOR.apply_settings(
            ImageSettings(
                fs=1e2,
            )
        )

    # Define Connections
    def network(self) -> ez.NetworkDefinition:
        return ((self.IMAGE_GENERATOR.OUTPUT, self.IMAGE_APP.INPUT),)

    def process_components(self):
        return (self.IMAGE_APP, self.IMAGE_GENERATOR)


def get_image():
    """Load an image from the demo-data repository if possible. Otherwise,
    just return a randomly generated image.
    """
    # generate random image
    image = np.random.normal(size=(256, 256))
    image[32:224, 32:224] += 3.0
    image[128] += 3.0
    image[:, 128] += 3.0
    image = ((image - image.min()) * (253.0 / (image.max() - image.min()))).astype(
        np.ubyte
    )
    return image


if __name__ == "__main__":
    system = ImageVisDemo()
    ez.run(SYSTEM=system)
