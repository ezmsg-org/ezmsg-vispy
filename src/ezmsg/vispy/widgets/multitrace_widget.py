import enum
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Optional

import numpy as np
from qtpy import QtWidgets

from vispy import color
from vispy import scene

from ..helpers.ranged_pan_zoom import RangedPanZoomCamera
from .base_plot_widget import BasePlotWidget

logger = logging.getLogger(__name__)

DEFAULT_COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def poly_coords(lx, cy, dx, dy):
    return [
        (lx, cy - dy / 2),
        (lx + dx, cy - dy / 2),
        (lx + 3 / 2 * dx, cy),
        (lx + dx, cy + dy / 2),
        (lx, cy + dy / 2),
    ]


class Coupling(enum.Enum):
    AC = enum.auto()
    DC = enum.auto()


class EditPolygon(scene.Polygon):
    def __init__(
        self,
        lx,
        cy,
        dx,
        dy,
        line: Optional[scene.Line] = None,
        scale_cb: Optional[Callable] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.unfreeze()
        self.lx = lx
        self.cy = cy
        self.dx = dx
        self.dy = dy
        self.line = line
        self.scale_cb = scale_cb
        self.interactive = True
        self.drag_reference = [0, 0]
        self.current_scale = None
        self.freeze()
        self.update_coords()

    def update_coords(self):
        pos = poly_coords(self.lx, self.cy, self.dx, self.dy)
        self.pos = pos
        if self.line is not None and self.line.transform is not None:
            self.line.transform.translate = (0, self.cy, 0)

    def start_move(self, start):
        self.drag_reference = start - self.center

    def start_scale(self, start):
        self.drag_reference = start - self.center
        if self.line is not None and self.line.transform is not None:
            self.current_scale = self.line.transform.scale[1]

    def set_line(self, line: scene.Line):
        self.line = line
        self.line.transform.translate = (0, self.cy, 0)

    def move(self, end):
        shift = end - self.drag_reference
        self.center = shift

    def scale(self, end):
        if self.line is not None and self.line.transform is not None:
            shift = end - self.drag_reference - self.cy
            self.line.transform.scale = (1, self.current_scale + shift)
            self.send_scale()

    def autoscale(self, num_divs=2.0):
        if self.line is not None and self.line.pos is not None:
            min_y, max_y = min(self.line.pos[:, 1]), max(self.line.pos[:, 1])
            scale = abs(max_y - min_y) + abs(np.mean(self.line.pos[:, 1])) * 1.5
            if scale != 0.0:
                self.line.transform.scale = (1, num_divs / scale)
            self.send_scale()

    def send_scale(self):
        if (
            self.scale_cb is not None
            and self.line is not None
            and self.line.transform is not None
        ):
            self.scale_cb(1 / (2 * self.line.transform.scale[1]))

    @property
    def center(self):
        return self.cy

    @center.setter
    def center(self, val):
        self.cy = val
        self.update_coords()


@dataclass
class MultiTraceData:
    data: np.ndarray
    fs: Optional[float] = None
    x_arr: Optional[np.ndarray] = None
    trace_name: str = "default"
    ch_names: Optional[Sequence[str]] = None
    units: Optional[str] = None


@dataclass
class TraceVisuals:
    line: scene.Line
    marker: EditPolygon
    coupling: Optional[Coupling] = None

    @property
    def visible(self):
        return self.line.visible and self.marker.visible

    @visible.setter
    def visible(self, val: bool):
        self.line.visible = val
        self.marker.visible = val

    def set_visible(self, val: bool):
        self.visible = val

    def set_coupling(self, val: str):
        coupling = Coupling[val.upper()]
        self.coupling = coupling


@dataclass
class TraceInfo:
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    traces: Sequence[TraceVisuals] = tuple()
    ch_tree: Sequence[bool] = tuple()
    channels: int = 0
    fs: Optional[float] = None


class MultiTraceMode(enum.Enum):
    ROLL = enum.auto()
    SET = enum.auto()


class ChannelWidget(QtWidgets.QFrame):
    def __init__(self, color, units=None, name=""):
        super().__init__()
        if units is None:
            self.units = "units"
        else:
            self.units = units
        self.color = color
        self.name = name

        self.checkbox_enabled = QtWidgets.QCheckBox()
        self.checkbox_enabled.setText(self.name)
        self.checkbox_enabled.setChecked(True)
        self.lb_scalediv = QtWidgets.QLabel()
        self.lb_scalediv.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.lb_color = QtWidgets.QLabel()
        self.lb_color.setStyleSheet(f"background-color: {self.color}")
        self.lb_color.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred
        )
        self.lb_color.setFixedWidth(15)

        self.cb_coupling = QtWidgets.QComboBox()
        self.cb_coupling.addItems([e.name.upper() for e in Coupling])
        # This is where we could override default setting.
        self.cb_coupling.setCurrentText(Coupling.DC.name.upper())

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(0)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        hlayout.addWidget(self.checkbox_enabled)
        hlayout.addWidget(self.lb_color)
        hwidget = QtWidgets.QWidget()
        hwidget.setLayout(hlayout)

        vlayout.addWidget(hwidget)
        vlayout.addWidget(self.lb_scalediv)
        vlayout.addWidget(self.cb_coupling)
        self.setLayout(vlayout)
        self.setFrameStyle(
            QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Raised
        )

    def update_scale(self, val):
        self.lb_scalediv.setText(f"{val:.3E} {self.units}/div")


class MultiTraceWidget(BasePlotWidget):
    WINDOW_WIDTH = 10
    WINDOW_HEIGHT = 10
    LX, CY, DX, DY = 0.0, WINDOW_HEIGHT // 2, 0.15, 0.2
    FILL_ALPHA = 0.1

    def __init__(
        self,
        mode: MultiTraceMode = MultiTraceMode.SET,
        trace_colors: dict[str, list] = None,
        *args,
        **kwargs,
    ):
        if trace_colors is None:
            trace_colors = dict()
        super().__init__(*args, **kwargs)

        self.mode = mode
        # Setup the default trace_colors
        self.trace_colors = trace_colors
        self.trace_colors["default"] = [
            color.Color(name).hex for name in DEFAULT_COLORS
        ]
        self.trace_colors["inuse"] = list()
        # trace_map will contain the source string as key and config info as val.
        self.trace_map: dict[str, TraceInfo] = dict()

        self.selected_object = None
        self.x_arr = None

        self._configure_2d()
        self.view.camera = RangedPanZoomCamera(vertical_zoom=True, vert_pan=False)
        # the left mouse button pan has to be disabled in the camera, as it
        # interferes with dragging line points
        if self.view.camera._viewbox is not None:
            self.view.camera._viewbox.events.mouse_move.disconnect(
                self.view.camera.viewbox_mouse_event
            )
        # Add custom overrides for mouse events.
        self.canvas.unfreeze()
        self.canvas.on_mouse_press = self.on_mouse_press
        self.canvas.on_mouse_double_click = self.on_mouse_double_click
        self.canvas.on_mouse_move = self.on_mouse_move
        # Create a new canvas for the markers
        self.marker_widget = self.canvas_grid.add_view(row=2, col=5)
        self.marker_widget.camera = "panzoom"
        if not (
            isinstance(self.marker_widget, scene.ViewBox)
            and isinstance(self.marker_widget.camera, scene.PanZoomCamera)
        ):
            raise ValueError("Marker Widget did not initialize correctly.")
        self.marker_widget.camera.flip = (True, False)
        self.marker_widget.camera.rect = (0, 0, 1.5 * self.DX, self.WINDOW_HEIGHT)
        if self.marker_widget.camera._viewbox is not None:
            self.marker_widget.camera._viewbox.events.mouse_move.disconnect(
                self.marker_widget.camera.viewbox_mouse_event
            )
        self.marker_widget.interactive = False
        self.marker_widget.width_max = 30
        self.marker_widget.width_min = 30
        if isinstance(self.marker_widget.camera, scene.PanZoomCamera):
            self.marker_widget.camera.link(self.view.camera, axis="y")
        self.canvas.freeze()

        # Add a QScrollArea for channel widgets.
        self.channel_scroll_area = QtWidgets.QScrollArea()
        self.channel_scroll_area.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.channel_scroll_area.setWidgetResizable(True)
        self.channel_scroll_area.setContentsMargins(0, 0, 0, 0)
        self.channel_scroll_w = QtWidgets.QWidget()
        self.channel_control_w = QtWidgets.QWidget()
        channel_control_layout = QtWidgets.QVBoxLayout()
        channel_control_layout.setSpacing(0)
        channel_control_layout.setContentsMargins(0, 0, 0, 0)
        self.channel_control_w.setLayout(channel_control_layout)
        scroll_layout = QtWidgets.QVBoxLayout()
        scroll_layout.addWidget(self.channel_control_w)
        scroll_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Preferred,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        scroll_layout.setSpacing(0)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.channel_scroll_w.setLayout(scroll_layout)

        self.channel_controls = dict()

        self.pb_pause_updates = QtWidgets.QPushButton("Pause")
        self.pb_pause_updates.clicked.connect(self.on_pause)
        self.pb_channelize = QtWidgets.QPushButton("Channelize")
        self.pb_channelize.clicked.connect(self.on_channelize)
        self.pb_overlay = QtWidgets.QPushButton("Overlay")
        self.pb_overlay.clicked.connect(self.on_overlay)

        self.paused = False

        control_widget = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout()
        control_layout.addWidget(self.pb_pause_updates)
        control_layout.addWidget(self.pb_channelize)
        control_layout.addWidget(self.pb_overlay)
        control_layout.addWidget(self.channel_scroll_area)
        control_widget.setLayout(control_layout)

        self.grid.addWidget(control_widget, 0, 9, 7, 1)

        # Link the Axes cameras and signals.
        self.link_views()

    def on_pause(self):
        if self.paused is True:
            self.pb_pause_updates.setText("Pause")
            self.paused = False
        else:
            self.pb_pause_updates.setText("Resume")
            self.paused = True

    def on_channelize(self):
        num_channels = sum([trace.channels for trace in self.trace_map.values()])
        spacing = self.WINDOW_HEIGHT / num_channels
        trace_count = 0
        for traceinfo in self.trace_map.values():
            for trace in traceinfo.traces[::-1]:
                trace.marker.autoscale(spacing)
                trace.marker.center = (trace_count + 0.5) * spacing
                trace_count += 1

    def on_overlay(self):
        for traceinfo in self.trace_map.values():
            for trace in traceinfo.traces[::-1]:
                trace.marker.autoscale(self.WINDOW_HEIGHT)
                trace.marker.center = self.WINDOW_HEIGHT / 2

    def on_mouse_press(self, event):
        self.view.interactive = False
        selected = self.canvas.visual_at(event.pos)
        self.view.interactive = True
        if self.selected_object is not None:
            self.selected_object = None

        if self.canvas.scene is not None and isinstance(selected, EditPolygon):
            self.selected_object = selected
            # update transform to selected object
            tr = self.canvas.scene.node_transform(self.selected_object)
            pos = tr.map(event.pos)
            # we only care about changes in y value.
            yval = pos[1]
            if event.button == 1:
                self.selected_object.start_move(yval)
            elif event.button == 2:
                self.selected_object.start_scale(yval)

    def on_mouse_double_click(self, event):
        if event.button == 1:
            if self.selected_object is not None:
                self.selected_object.autoscale()

    def on_mouse_move(self, event):
        if self.view.camera._viewbox is not None and self.canvas.scene is not None:
            if self.selected_object is not None:
                self.view.camera._viewbox.events.mouse_move.disconnect(
                    self.view.camera.viewbox_mouse_event
                )
                # update transform to selected object
                tr = self.canvas.scene.node_transform(self.selected_object)
                pos = tr.map(event.pos)
                # we only care about changes in y value.
                yval = pos[1]
                if event.button == 1:
                    self.selected_object.move(yval)
                elif event.button == 2:
                    self.selected_object.scale(yval)
            else:
                self.view.camera._viewbox.events.mouse_move.connect(
                    self.view.camera.viewbox_mouse_event
                )

    def roll_data(self, message: MultiTraceData):
        # Incoming data should be time_dim x ch_dim
        new_data = message.data
        fs = message.fs
        trace_name = message.trace_name
        trace_info: Optional[TraceInfo] = self.trace_map.get(trace_name, None)

        if fs is None:
            raise Exception(
                "MultiTraceWidget.roll_data() must be passed sampling rate (fs)."
            )
        if (
            trace_info is None
            or new_data.shape[1] != trace_info.channels
            or fs != trace_info.fs
        ):
            trace_info = self.update_trace(message)

        if isinstance(trace_info, TraceInfo):
            num_data_pts = new_data.shape[0]
            # Get the current vertex buffer of the plot.
            data = trace_info.data
            # Make sure the number of new data pts does not exceed window length
            if num_data_pts > data.shape[1]:
                logger.warn("Number of data points exceeds length of window!")
                logger.warn(f"Number of data points: {num_data_pts}")
                logger.warn(f"Length of window: {data.shape[1]}")
            # Flip the data
            new_data = new_data.T
            new_data = np.flip(new_data, axis=1)
            data[:, num_data_pts:, 1] = data[:, :-num_data_pts, 1]
            data[:, :num_data_pts, 1] = new_data
            if self.paused is False:
                for idx, visuals in enumerate(trace_info.traces):
                    if visuals.coupling is not None and visuals.coupling is Coupling.AC:
                        demean_data = data[idx].copy()
                        demean_data[:, 1] -= np.mean(demean_data[:, 1])
                        visuals.line.set_data(pos=demean_data)
                    else:
                        visuals.line.set_data(pos=data[idx])

    def set_data(self, message: MultiTraceData):
        new_data = message.data
        fs = message.fs
        x_arr = message.x_arr
        trace_name = message.trace_name
        trace_info: Optional[TraceInfo] = self.trace_map.get(trace_name, None)
        if (
            trace_info is None
            or new_data.shape[1] != trace_info.channels
            or new_data.shape[0] != trace_info.data.shape[1]
            or fs != trace_info.fs
        ):
            trace_info = self.update_trace(message)

        if x_arr is None:
            # Grab the xarr we generated when updating trace.
            x_arr = self.x_arr

        if type(x_arr) != np.ndarray:
            logger.warning(f"x_arr must be an np.ndarray, not {type(x_arr)}")
        elif x_arr.shape[0] != new_data.shape[0]:
            logger.warning("Time dimensions must match for timestamps and data!")
            logger.warning(
                f"x_arr shape = {x_arr.shape}, data shape = {new_data.shape}"
            )
        else:
            data = trace_info.data
            data[:, :, 0] = x_arr
            data[:, :, 1] = new_data.T
            if self.paused is False:
                for idx, visuals in enumerate(trace_info.traces):
                    if visuals.coupling is not None and visuals.coupling is Coupling.AC:
                        demean_data = data[idx].copy()
                        demean_data[:, 1] -= np.mean(demean_data[:, 1])
                        visuals.line.set_data(pos=demean_data)
                    else:
                        visuals.line.set_data(pos=data[idx])

    def update_trace(self, message: MultiTraceData) -> TraceInfo:
        data = message.data
        channels = data.shape[1]
        fs = message.fs
        x_arr = message.x_arr
        trace_name = message.trace_name
        ch_names = message.ch_names
        units = message.units

        self.x_arr = None

        if not isinstance(self.view.camera, RangedPanZoomCamera):
            raise ValueError("Camera is not of expected type.")
        if not isinstance(self.marker_widget, scene.ViewBox):
            raise ValueError("MarkerWidget not initialized before update_trace.")

        if trace_name in self.channel_controls:
            widget = self.channel_controls[trace_name]
            widget.setParent(None)
        if trace_name in self.trace_map:
            for visuals in self.trace_map[trace_name].traces:
                visuals.line.parent = None
                if visuals.line.color is not None:
                    self.trace_colors["inuse"].remove(visuals.line.color.hex)
                visuals.marker.parent = None

        if self.mode == MultiTraceMode.ROLL:
            if fs is None:
                raise ValueError("Must specify fs if in ROLL mode.")

            # Set limits on the camera
            rect = (0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

            self.view.camera.limits = rect
            self.view.camera.rect = rect
            # Flip the camera for updating the data
            self.view.camera.flip = (True, False)

            ch_buf_len = int(self.WINDOW_WIDTH * fs)
            dt = 1 / fs

            # Setup the initial position buffer.
            pos = np.zeros(
                (channels, ch_buf_len, 2),
                np.float32,
            )
            pos[:, :, 0] = np.arange(start=0, stop=self.WINDOW_WIDTH, step=dt)[
                :ch_buf_len
            ]

        elif self.mode == MultiTraceMode.SET:
            if x_arr is None:
                if fs is not None:
                    x_arr = np.arange(0.0, (1 / fs) * data.shape[0], 1 / fs)[
                        : data.shape[0]
                    ]
                    self.x_arr = x_arr
                else:
                    raise Exception
            # Set limits on the camera
            rect = (x_arr[0], 0, x_arr[-1] - x_arr[0], self.WINDOW_HEIGHT)
            self.view.camera.limits = rect
            self.view.camera.rect = rect

            # Setup the initial position buffer.
            pos = np.zeros(
                (channels, x_arr.shape[0], 2),
                np.float32,
            )
            pos[:, :, 0] = x_arr
        else:
            logger.error("Multitrace mode not valid!")
            raise Exception

        # Setup the color array. Remove any colors that are already in use
        if trace_name in self.trace_colors:
            colors = self.trace_colors[trace_name]
            diff = set(colors) - set(self.trace_colors["inuse"])
            colors = [color for color in colors if color in diff]
        else:
            colors = self.trace_colors["default"]
        # Add the line and marker visuals to the scene
        channel_container = QtWidgets.QGroupBox(trace_name)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        traces = []
        for ch in range(channels):
            if ch >= len(colors):
                ch = ch % len(colors)
            c = color.Color(colors[ch])
            self.trace_colors["inuse"].append(c.hex)
            if ch_names is None:
                name = f"Channel {ch}"
            else:
                name = ch_names[ch]
            channel_widget = ChannelWidget(color=c.hex, name=name, units=units)
            line = scene.Line(pos[ch], color=c, parent=self.view.scene)  # type: ignore
            line.transform = scene.STTransform()
            marker = EditPolygon(
                self.LX,
                self.CY,
                self.DX,
                self.DY,
                line=line,
                scale_cb=channel_widget.update_scale,
                color=color.Color(c, alpha=self.FILL_ALPHA),  # type: ignore
                border_color=c,
                parent=self.marker_widget.scene,
            )
            visuals = TraceVisuals(line, marker)

            def update_coupling():
                coupling = Coupling[channel_widget.cb_coupling.currentText()]
                visuals.coupling = coupling

            traces.append(visuals)
            layout.addWidget(channel_widget)
            marker.autoscale()
            channel_widget.checkbox_enabled.stateChanged.connect(visuals.set_visible)
            channel_widget.cb_coupling.currentTextChanged.connect(visuals.set_coupling)
        channel_container.setLayout(layout)
        self.channel_controls[trace_name] = channel_container
        channel_control_layout = self.channel_control_w.layout()
        if channel_control_layout is not None:
            channel_control_layout.addWidget(channel_container)
        self.channel_scroll_area.setWidget(self.channel_scroll_w)

        trace_info = TraceInfo(
            data=pos,
            traces=traces,
            ch_tree=[True] * channels,
            channels=channels,
            fs=fs,
        )
        self.trace_map[trace_name] = trace_info
        return trace_info
