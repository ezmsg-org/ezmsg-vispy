import logging
from PyQt6 import QtWidgets, QtCore
from typing import Union, Optional
from dataclasses import dataclass
from vispy import scene

from vispy.visuals import ColorBarVisual

ColorBarVisual.text_padding_factor = 1.6

logger = logging.getLogger(__name__)


@dataclass
class AxisConfig:
    enabled: bool
    position: str
    type: str


@dataclass
class CbarConfig:
    enabled: bool
    position: str
    cmap: str
    label: str


@dataclass
class LabelConfig:
    position: str
    text: Optional[str]


# Inspired by the Vispy PlotWidget
# https://github.com/vispy/vispy/blob/main/vispy/plot/plotwidget.py
class BasePlotWidget(QtWidgets.QWidget):
    """
    Widget to facilitate plotting. Creates PyQt and Vispy layouts for
    title, xaxis, yaxis, etc.

    Parameters
    ----------
    title : str | None
        The title string to be displayed above the plot
    xax_en : bool
        Enable X axis.
    yax_en : bool
        Enable Y axis.
    xax_pos : str
        Position of X axis. May be "top" or "bottom"
    yax_pos : str
        Position of Y axis. May be "left" or "right"
    xax_type: str
        Type of X axis. May be "pyqt", "vispy", or "custom"
    yax_type: str
        Type of Y axis. May be "pyqt", "vispy", or "custom"
    xlabel : str | None
        The label to display along the x axis.
    ylabel : str | None
        The label to display along the y axis.
    xlabel_pos : str
        Position of X label. May be "top" or "bottom"
    ylabel_pos : str
        Position of Y label. May be "left" or "right"
    gridlines_en : bool
        Enable Gridlines on the visual view.
    fg_color: str
        Color of the plot foreground.
    bg_color: str
        Color of the plot background.
    """

    LEFT_PADDING_MIN: int = 0
    LEFT_PADDING_MAX: int = 0
    RIGHT_PADDING_MIN: int = 0
    RIGHT_PADDING_MAX: int = 0
    BOTTOM_PADDING_MIN: int = 0
    BOTTOM_PADDING_MAX: int = 0

    grid: QtWidgets.QGridLayout
    xlabel: Union[QtWidgets.QLabel, QtWidgets.QWidget]
    ylabel: Union[QtWidgets.QLabel, QtWidgets.QWidget]
    xaxis: Union[QtWidgets.QWidget, scene.AxisWidget]
    yaxis: Union[QtWidgets.QWidget, scene.AxisWidget]

    visibility_change_ev = QtCore.pyqtSignal(bool)

    def __init__(
        self,
        title: Optional[str] = None,
        xax_en: bool = False,
        yax_en: bool = False,
        xax_pos: str = "bottom",
        yax_pos: str = "left",
        xax_type: str = "vispy",
        yax_type: str = "vispy",
        cbar_en: bool = False,
        cbar_pos: str = "right",
        cbar_cmap: str = "grays",
        cbar_label: str = "",
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        xlabel_pos: str = "bottom",
        ylabel_pos: str = "left",
        gridlines_en: bool = False,
        fg_color="w",
        bg_color="k",
    ):
        super().__init__()
        # Parse Args
        self._fg = fg_color
        self._bg = bg_color
        self._xax_conf = AxisConfig(xax_en, xax_pos, xax_type)
        self._yax_conf = AxisConfig(yax_en, yax_pos, yax_type)
        self._xlabel_conf = LabelConfig(xlabel_pos, xlabel)
        self._ylabel_conf = LabelConfig(ylabel_pos, ylabel)
        self._gridlines_en = gridlines_en
        self._cbar_conf = CbarConfig(cbar_en, cbar_pos, cbar_cmap, cbar_label)

        # Members
        self.camera = None
        self.cbar = None
        self._configured = False

        self.grid = QtWidgets.QGridLayout(self)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.title = QtWidgets.QLabel(title)
        self.title.font().setPointSize(16)
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.grid)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # self.installEventFilter(self)

    def eventFilter(self, o, e):
        if o is self:
            if e.type() == QtCore.QEvent.Type.Show:
                print("Visible")
            elif e.type() == QtCore.QEvent.Type.Hide:
                print("Hidden")
        return False

    def _configure_2d(self):
        if self._configured:
            return

        #     c0        c1      c2      c3      c4      c5      c6      c7        c8
        #  r0 +---------+-------+-------+-------+--------+-------+-------+---------+---------+
        #     |         |                       | title  |               |         |         |
        #  r1 |         +-----------------------+--------+---------------+---------+         |
        #     |         |                       | cbar   |               |         |         |
        #  r2 |         +-------+-------+-------+--------+-------+-------+---------+         |
        #     |         |                       | xlabel |               |         |         |
        #  r3 |         +-----------------------+--------+---------------+---------+         |
        #     |         |                       | xaxis  |               |         |         |
        #  r4 |         +-----------------------+--------+---------------+---------+         |
        #     |         | cbar  | ylabel| yaxis | visual | yaxis | ylabel| cbar    |         |
        #  r5 | padding +-------+-------+-------+--------+-------+-------+---------+ padding |
        #     |         |                       | xaxis  |               |         |         |
        #  r6 |         +-----------------------+--------+---------------+---------+         |
        #     |         |                       | xlabel |               |         |         |
        #  r7 |         +-----------------------+--------+---------------+---------+         |
        #     |         |                       | cbar   |               |         |         |
        #  r8 |---------+-----------------------+--------+---------------+---------+---------|
        #     |                                  padding                                     |
        #     +---------+-----------------------+--------+---------------+---------+---------+
        #
        # The visual will also have a layout for axes.
        # This gives the end-user the option to use a simple PyQt axes widgets, or Vispy's AxisWidget.
        #     c0      c1      c2      c3      c4
        #  r0 +------+-------+-------+-------+------+
        #     |      |       | cbar  |       |      |
        #  r1 |------+-------+-------+-------+------|
        #     |      |       | xaxis |       |      |
        #  r2 |------+-------+-------+-------+------|
        #     | cbar | yaxis | view  | yaxis | cbar |
        #  r3 |------+-------+-------+-------+------|
        #     |      |       | xaxis |       |      |
        #  r4 |------+-------+-------+-------+------|
        #     |      |       | cbar  |       |      |
        #     +------+-------+-------+-------+------+

        # padding left
        padding_left = QtWidgets.QWidget(self)
        self.grid.addWidget(padding_left, 0, 0, 7, 1)
        padding_left.setMinimumWidth(self.LEFT_PADDING_MIN)
        padding_left.setMaximumWidth(self.LEFT_PADDING_MAX)
        # padding right
        padding_right = QtWidgets.QWidget(self)
        self.grid.addWidget(padding_right, 0, 8, 7, 1)
        padding_right.setMinimumWidth(self.RIGHT_PADDING_MIN)
        padding_right.setMaximumWidth(self.RIGHT_PADDING_MAX)
        # padding bottom
        padding_bottom = QtWidgets.QWidget(self)
        self.grid.addWidget(padding_bottom, 8, 0, 1, 8)
        padding_bottom.setMinimumHeight(self.BOTTOM_PADDING_MIN)
        padding_bottom.setMaximumHeight(self.BOTTOM_PADDING_MAX)

        # row 0
        # title - column 4
        if self.title.text() != "":
            self.grid.addWidget(self.title, 0, 4)

        # row 2
        # xlabel - column 4
        if self._xlabel_conf.position == "top" and self._xlabel_conf.text is not None:
            self.xlabel = QtWidgets.QLabel(self._xlabel_conf.text)
            self.xlabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.xlabel.setMargin(10)
            self.grid.addWidget(self.xlabel, 2, 4)

        # row 3
        # xaxis - column 4
        if (
            self._xax_conf.enabled is True
            and self._xax_conf.position == "top"
            and self._xax_conf.type == "pyqt"
        ):
            # Add custom xaxis here
            self.xaxis = QtWidgets.QWidget()
            self.grid.addWidget(self.xlabel, 3, 4)
            self.xlabel.setMaximumHeight(40)

        # row 4
        # ylabel - column 2
        if self._ylabel_conf.position == "left":
            if self._ylabel_conf.text is not None:
                self.ylabel = QtWidgets.QLabel(self._ylabel_conf.text)
                self.ylabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.ylabel.setMargin(10)
            else:
                self.ylabel = QtWidgets.QWidget()
            self.grid.addWidget(self.ylabel, 4, 2)
        # yaxis - column 3
        if (
            self._yax_conf.enabled is True
            and self._yax_conf.position == "left"
            and self._yax_conf.type == "pyqt"
        ):
            # Add custom xaxis here
            self.yaxis = QtWidgets.QWidget()
            self.grid.addWidget(self.yaxis, 3, 4)

        # view - column 4
        self.canvas = scene.SceneCanvas()
        self.canvas_grid = self.canvas.central_widget.add_grid(spacing=0, margin=0)

        if (
            self._yax_conf.enabled is True
            and self._yax_conf.position == "left"
            and self._yax_conf.type == "vispy"
        ):
            self.yaxis = scene.AxisWidget(
                orientation="left",
                text_color=self._fg,
                axis_color=self._fg,
                tick_color=self._fg,
            )
            yaxis_widget = self.canvas_grid.add_widget(self.yaxis, row=2, col=1)
            yaxis_widget.width_max = 60
            yaxis_widget.width_min = 60
        else:
            widget = self.canvas_grid.add_widget(None, row=2, col=1)
            widget.width_max = 0

        if (
            self._yax_conf.enabled is True
            and self._yax_conf.position == "right"
            and self._yax_conf.type == "vispy"
        ):
            self.yaxis = scene.AxisWidget(
                orientation="right",
                text_color=self._fg,
                axis_color=self._fg,
                tick_color=self._fg,
            )
            yaxis_widget = self.canvas_grid.add_widget(self.yaxis, row=2, col=3)
            yaxis_widget.width_max = 60
            yaxis_widget.width_min = 60
        else:
            widget = self.canvas_grid.add_widget(None, row=2, col=3)
            widget.width_max = 0

        if (
            self._xax_conf.enabled is True
            and self._xax_conf.position == "top"
            and self._xax_conf.type == "vispy"
        ):
            self.xaxis = scene.AxisWidget(
                orientation="top",
                text_color=self._fg,
                axis_color=self._fg,
                tick_color=self._fg,
                axis_label_margin=20,
            )
            xaxis_widget = self.canvas_grid.add_widget(self.xaxis, row=1, col=2)
            xaxis_widget.height_max = 40
            xaxis_widget.height_min = 40
        else:
            widget = self.canvas_grid.add_widget(None, row=1, col=2)
            widget.height_max = 0
        if (
            self._xax_conf.enabled is True
            and self._xax_conf.position == "bottom"
            and self._xax_conf.type == "vispy"
        ):
            self.xaxis = scene.AxisWidget(
                orientation="bottom",
                text_color=self._fg,
                axis_color=self._fg,
                tick_color=self._fg,
                axis_label_margin=20,
            )
            xaxis_widget = self.canvas_grid.add_widget(self.xaxis, row=3, col=2)
            xaxis_widget.height_max = 40
            xaxis_widget.height_min = 40
        else:
            widget = self.canvas_grid.add_widget(None, row=3, col=2)
            widget.height_max = 0

        # Create colorbar placeholders
        cbar_top = self.canvas_grid.add_widget(None, row=0, col=2)
        cbar_top.height_max = 0
        cbar_bottom = self.canvas_grid.add_widget(None, row=4, col=2)
        cbar_bottom.height_max = 0
        cbar_left = self.canvas_grid.add_widget(None, row=2, col=0)
        cbar_left.width_max = 0
        cbar_right = self.canvas_grid.add_widget(None, row=2, col=4)
        cbar_right.width_max = 0
        # Fill in cbar if enabled
        if self._cbar_conf.enabled is True:
            self.cbar = scene.ColorBarWidget(
                orientation=self._cbar_conf.position,
                label=self._cbar_conf.label,
                label_color=self._fg,
                cmap=self._cbar_conf.cmap,
                border_width=1,
                border_color=self._fg,
            )
            for tick in self.cbar._colorbar._ticks:
                tick.font_size = 8.0
                if self.cbar.orientation == "left" or self.cbar.orientation == "right":
                    tick.rotation = 90.0

            if self.cbar.orientation == "bottom":
                self.canvas_grid.remove_widget(cbar_bottom)
                self.cbar.height_max = self.cbar.height_min = 90
                self.canvas_grid.add_widget(self.cbar, row=4, col=2)
            elif self.cbar.orientation == "top":
                self.canvas_grid.remove_widget(cbar_top)
                self.canvas_grid.add_widget(self.cbar, 0, 2)
                self.cbar.height_max = self.cbar.height_min = 90
            elif self.cbar.orientation == "left":
                self.canvas_grid.remove_widget(cbar_left)
                self.canvas_grid.add_widget(self.cbar, 2, 0)
                self.cbar.width_max = self.cbar.width_min = 90
            elif self.cbar.orientation == "right":
                self.canvas_grid.remove_widget(cbar_right)
                self.canvas_grid.add_widget(self.cbar, 2, 4)
                self.cbar.width_max = self.cbar.width_min = 90
            else:
                raise ValueError(f"Invalid colorbar location: {self.cbar.orientation}")

        # self.view = self.canvas_grid.add_view()
        self.view = scene.ViewBox()
        self.canvas_grid.add_widget(self.view, row=2, col=2)
        self.view.camera = "panzoom"
        self.camera = self.view.camera
        self.canvas.bgcolor = self._bg
        self.central_widget = self.canvas.native
        self.central_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.grid.addWidget(self.central_widget, 4, 4)

        # Add gridlines if enabled
        if self._gridlines_en is True:
            self.gridlines = scene.GridLines(parent=self.view.scene)  # type: ignore

        # yaxis - column 5
        if (
            self._yax_conf.enabled is True
            and self._yax_conf.position == "right"
            and self._yax_conf.type == "pyqt"
        ):
            # Add custom xaxis here
            self.yaxis = QtWidgets.QWidget()
            self.grid.addWidget(self.yaxis, 4, 5)

        # ylabel - column 6
        if self._ylabel_conf.position == "right":
            if self._ylabel_conf.text is not None:
                self.ylabel = QtWidgets.QLabel(self._ylabel_conf.text)
                self.ylabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.ylabel.setMargin(10)
            else:
                self.ylabel = QtWidgets.QWidget()
            self.grid.addWidget(self.ylabel, 4, 6)

        # row 5
        # xaxis - column 4
        if (
            self._xax_conf.enabled is True
            and self._xax_conf.position == "bottom"
            and self._xax_conf.type == "pyqt"
        ):
            # Add custom xaxis here
            self.xaxis = QtWidgets.QWidget()
            self.grid.addWidget(self.xlabel, 3, 4)
            self.xlabel.setMaximumHeight(40)

        # row 6
        # xlabel - column 4
        if (
            self._xlabel_conf.position == "bottom"
            and self._xlabel_conf.text is not None
        ):
            self.xlabel = QtWidgets.QLabel(self._xlabel_conf.text)
            self.xlabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.xlabel.setMargin(10)
            self.grid.addWidget(self.xlabel, 6, 4)

        self.link_views()
        self._configured = True

    def link_views(self):
        if (
            self._xax_conf.enabled is True
            and self._xax_conf.type == "vispy"
            and type(self.xaxis) is scene.AxisWidget
        ):
            self.xaxis._linked_view = None
            self.xaxis.link_view(self.view)
        if (
            self._yax_conf.enabled is True
            and self._yax_conf.type == "vispy"
            and type(self.yaxis) is scene.AxisWidget
        ):
            self.yaxis._linked_view = None
            self.yaxis.link_view(self.view)

    def update(self):
        raise NotImplementedError

    def setVisible(self, visible: bool) -> None:
        self.visibility_change_ev.emit(visible)
        return super().setVisible(visible)
