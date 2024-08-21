import logging

import numpy as np
from qtpy import QtWidgets

from vispy import scene

from ..helpers.axis_widgets import create_yaxes
from ..helpers.axis_widgets import create_ylabels
from ..helpers.channel_magnification import ChannelFocusTransform
from ..helpers.constants import LINE_COLORS
from ..helpers.ranged_pan_zoom import RangedPanZoomCamera
from .base_plot_widget import BasePlotWidget

logger = logging.getLogger(__name__)


"""
Deprecated: This class is no longer recommended for use.
Please consider using the MultiTraceWidget class instead.
"""


class MultiLineWidget(BasePlotWidget):
    def __init__(
        self,
        pos=None,
        color=(0.5, 0.5, 0.5, 1),
        width=1,
        connect="strip",
        method="gl",
        antialias=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._configure_2d()
        self.view.camera = RangedPanZoomCamera(vertical_zoom=False, vert_pan=False)
        # the left mouse button pan has to be disabled in the camera, as it
        # interferes with dragging line points
        self.view.camera._viewbox.events.mouse_move.disconnect(
            self.view.camera.viewbox_mouse_event
        )
        # Add custom overrides for mouse events.
        self.canvas.unfreeze()
        self.canvas.on_mouse_press = self.on_mouse_press
        self.canvas.on_mouse_double_click = self.on_mouse_double_click
        self.canvas.on_mouse_move = self.on_mouse_move
        self.canvas.freeze()

        # Add the line visual to the scene
        self.line = scene.Line(
            pos, color, width, connect, method, antialias, parent=self.view.scene
        )
        # Transforms will be used to create
        # the multiple independent channel look.
        self.magnify_chain = scene.transforms.ChainTransform()
        self.line.transform = self.magnify_chain

        self.num_segments = None
        self.ch_selection = None
        self.seg_offset = 1
        self.seg_offset_arr = None

        self.mouse_start_pos = None
        self.ch_select = None
        self.prev_mag = None
        self.flip = True
        if self.flip is True:
            self.view.camera.flip = (True, False)

        self._update_yax = False
        # Link the Axes cameras and signals.
        self.link_views()

    def on_mouse_press(self, event):
        tr = self.canvas.scene.node_transform(self.view.scene)
        pos = tr.map(event.pos)
        # Define selected channel here
        if event.button == 2:  # right button deletes object
            self.ch_select = int((self.num_segments - 1) - (pos[1] // self.seg_offset))
            self.mouse_start_pos = pos
            self.prev_mag = self.magnify_chain.transforms[self.ch_select].mag

    def on_mouse_double_click(self, event):
        tr = self.canvas.scene.node_transform(self.view.scene)
        pos = tr.map(event.pos)
        # Define selected channel here
        self.ch_select = int((self.num_segments - 1) - (pos[1] // self.seg_offset))
        dat = self.line.pos
        dat = dat.reshape(self.num_segments, self.ch_buf_len, 2)
        max_y_val = np.max(
            np.abs(dat[self.ch_select, :, 1] - self.seg_offset_arr[self.ch_select])
        )
        # Now scale the channel to fit the window
        self.magnify_chain.transforms[self.ch_select].mag = (
            self.seg_offset / 2
        ) / max_y_val
        self.update_y_axes()

    def on_mouse_move(self, event):
        if event.button == 1:
            self.view.camera._viewbox.events.mouse_move.connect(
                self.view.camera.viewbox_mouse_event
            )
        elif event.button == 2:
            self.view.camera._viewbox.events.mouse_move.disconnect(
                self.view.camera.viewbox_mouse_event
            )
            tr = self.canvas.scene.node_transform(self.view.scene)
            pos = tr.map(event.pos)
            mag = 2 ** (1.5 * (pos - self.mouse_start_pos)[:2])[1] / self.seg_offset
            self.magnify_chain.transforms[self.ch_select].mag = self.prev_mag * mag
            self.view.camera.view_changed()
            self.update_y_axes()
        else:
            None

    def autoscale_channels(self):
        dat = self.line.pos
        dat = dat.reshape(self.num_segments, self.ch_buf_len, 2)
        max_y_val = np.max(np.abs(dat[:, :, 1] - self.seg_offset_arr))
        scale = (self.seg_offset / 2) / max_y_val
        for trans in self.magnify_chain.transforms:
            trans.mag = scale
        self.update_y_axes()

    def update_y_axes(self):
        def get_val(ch):
            return self.seg_offset / 2 / self.magnify_chain.transforms[ch].mag
        out = [round(get_val(ch) * 1e6, 3) for ch in range(self.num_segments)]
        for idx, val in enumerate(out):
            ax = self.yaxis.layout().itemAt(idx).widget()
            val = val
            top = str(val)
            bottom = str(-val)
            ax.top_label.setText(top)
            ax.bottom_label.setText(bottom)

    def roll_data(self, new_data, ch_mins=None, ch_maxs=None):
        # Data passed here should be of format ch x samples
        if not any(self.ch_selection):
            # If no channels are currently displayed, return.
            return
        # Add the correct offset to each channel.
        new_data = (
            new_data[self.ch_selection] + self.seg_offset_arr[: sum(self.ch_selection)]
        )
        _, num_data_pts = new_data.shape
        # Get the current vertex buffer of the plot.
        data = self.line.pos
        # Reshape into channels.
        data = data.reshape(self.num_segments, self.ch_buf_len, 2)
        # Make sure the number of new data pts does not exceed window length
        if num_data_pts > data.shape[1]:
            logger.warn("Number of data points exceeds length of window!")
            logger.warn(f"Number of data points: {num_data_pts}")
            logger.warn(f"Length of window: {data.shape[1]}")
        # Flip the data
        new_data = np.flip(new_data, axis=1)
        data[:, num_data_pts:, 1] = data[:, :-num_data_pts, 1]
        data[:, :num_data_pts, 1] = new_data
        self.line.set_data(pos=data)

        if self._update_yax is True:
            self.update_y_axes()
            self._update_yax = False

    def configure_segments(
        self, window_length, fs, channel_offset, num_segments=None, ch_selection=None
    ):
        if num_segments is None and ch_selection is None:
            raise "Must pass either number of waveforms or the currect channel selection!"

        if ch_selection is not None:
            self.ch_selection = ch_selection
        else:
            # Start by displaying all channels, user may deselect individual channels later.
            self.ch_selection = [True] * num_segments
        self.num_segments = sum(self.ch_selection)

        self.seg_offset = channel_offset
        self.ch_buf_len = int(window_length * fs)
        self.window_length = self.ch_buf_len / fs
        self.dt = 1 / fs
        self.N = self.ch_buf_len * self.num_segments

        # Set limits on the camera
        rect = (0, 0, self.window_length, self.num_segments * self.seg_offset)
        self.view.camera.limits = rect
        self.view.camera.rect = rect

        # Setup the vertex connection array.
        connect = np.ndarray(shape=(self.num_segments, self.ch_buf_len), dtype=np.bool8)
        connect[:, :-1] = True
        connect[:, -1] = False

        # Setup the initial position buffer.
        pos = np.empty(
            (self.num_segments, self.ch_buf_len, 2),
            np.float32,
        )
        pos[:, :, 0] = np.arange(start=0, stop=self.window_length, step=self.dt)
        pos[:, :, 1] = np.zeros(shape=(self.num_segments, self.ch_buf_len))

        self.seg_offset_arr = np.array(
            [
                [(self.num_segments - (i + 1)) * self.seg_offset + self.seg_offset / 2]
                for i in range(self.num_segments)
            ]
        )
        pos[:, :, 1] += self.seg_offset_arr

        # Setup the color array.
        color = np.empty((self.num_segments, self.ch_buf_len, 4), dtype=np.float32)
        color[:] = np.array(
            [
                [LINE_COLORS[idx][0].rgba]
                for idx, active in enumerate(self.ch_selection)
                if active
            ],
            dtype=np.float32,
        )

        # Setup the magnify transforms per channel.
        self.magnify_chain.transforms = [
            ChannelFocusTransform(
                mag=1.0, ch_width=(self.seg_offset / 2) * 0.999999, center=(0.0, offset)
            )
            for offset in self.seg_offset_arr
        ]

        # Finally, set the buffer data for the visual.
        self.line.set_data(
            connect=connect.reshape(
                self.N,
            ),
            pos=pos,
            color=color.reshape(self.N, 4),
        )
        # self.line.set_data(connect = connect ,pos = pos, color = color)

        self.yaxis.setLayout(create_yaxes(self.ch_selection, "um/s"))
        self.ylabel.setLayout(create_ylabels(self.ch_selection))
        yspacer = QtWidgets.QWidget()
        yspacer.setFixedHeight(40)
        # if self.xaxis is not None:
        # self.xaxis.native.setFixedHeight(40)
        self.yaxis.layout().addWidget(yspacer, self.num_segments)
        self.yaxis.setStyleSheet(
            "background-color: black; color: white; "
            + "border-right: 1px solid white; margin-left:3px;"
        )
        self.ylabel.layout().addWidget(yspacer, self.num_segments)
        self.ylabel.setStyleSheet(
            "background-color: black; color: white; "
            + "border-right: 1px solid white; margin-left:3px;"
        )
        self._update_yax = True
