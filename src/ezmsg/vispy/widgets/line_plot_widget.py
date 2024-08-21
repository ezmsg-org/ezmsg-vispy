from vispy import scene

from ..helpers.ranged_pan_zoom import RangedPanZoomCamera
from .base_plot_widget import BasePlotWidget


class LinePlotWidget(BasePlotWidget):
    """Plot a series of data using lines and markers
    Parameters
    ----------
    data : array | two arrays
        Arguments can be passed as ``(Y,)``, ``(X, Y)`` or
        ``np.array((X, Y))``.
    color : instance of Color
        Color of the line.
    symbol : str
        Marker symbol to use.
    line_kind : str
        Kind of line to draw. For now, only solid lines (``'-'``)
        are supported.
    width : float
        Line width.
    marker_size : float
        Marker size. If `size == 0` markers will not be shown.
    edge_color : instance of Color
        Color of the marker edge.
    face_color : instance of Color
        Color of the marker face.
    edge_width : float
        Edge width of the marker.
    connect : str | array
        Determines which vertices are connected by lines.
    *args : list
        Positional arguments to pass to `BasePlotWidget`.
    **kwargs : dict
        Keyword arguments to pass to `BasePlotWidget`.
    """

    def __init__(
        self,
        data,
        color="k",
        symbol=None,
        line_kind="-",
        width=1.0,
        marker_size=10.0,
        edge_color="k",
        face_color="b",
        edge_width=1.0,
        connect="strip",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._configure_2d()
        self.view.camera = RangedPanZoomCamera(aspect=1)
        self.line = scene.LinePlot(
            data,
            connect=connect,
            color=color,
            symbol=symbol,
            line_kind=line_kind,
            width=width,
            marker_size=marker_size,
            edge_color=edge_color,
            face_color=face_color,
            edge_width=edge_width,
            parent=self.view.scene,  # type: ignore
        )
        self.link_views()
