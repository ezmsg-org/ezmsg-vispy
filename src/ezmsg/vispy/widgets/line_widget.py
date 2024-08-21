from vispy import scene

from .base_plot_widget import BasePlotWidget


class LineWidget(BasePlotWidget):
    def __init__(
        self,
        pos=None,
        color=(0.5, 0.5, 0.5, 1),
        width=1,
        connect="strip",
        method="gl",
        antialias=False,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._configure_2d()
        # Add the line visual to the scene
        self.visual = scene.Line(
            pos, color, width, connect, method, antialias, parent=self.view.scene  # type: ignore
        )
        self.link_views()
