from typing import Optional

import numpy as np

from vispy import scene

from .base_plot_widget import BasePlotWidget


class HistogramWidget(BasePlotWidget):
    x_range: Optional[tuple[float, float]]
    y_range: Optional[tuple[float, float]]

    def __init__(self, color="w", orientation="h", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orientation = orientation

        self._configure_2d()
        self.visual = scene.Mesh(color=color, parent=self.view.scene)
        self.link_views()

        self.x_range = None
        self.y_range = None

    def update(self, data, bin_edges):
        if self.orientation == "v":
            X, Y = (0, 1)
        else:
            X, Y = (1, 0)

        # construct our vertices
        rr = np.zeros((3 * len(bin_edges) - 2, 3), np.float32)
        rr[:, X] = np.repeat(bin_edges, 3)[1:-1]
        rr[1::3, Y] = data
        rr[2::3, Y] = data
        bin_edges.astype(np.float32)
        # and now our tris
        tris = np.zeros((2 * len(bin_edges) - 2, 3), np.uint32)
        offsets = 3 * np.arange(len(bin_edges) - 1, dtype=np.uint32)[:, np.newaxis]
        tri_1 = np.array([0, 2, 1])
        tri_2 = np.array([2, 0, 3])
        tris[::2] = tri_1 + offsets
        tris[1::2] = tri_2 + offsets
        self.visual.set_data(rr, tris)
        x_range = (min(bin_edges), max(bin_edges))
        y_range = (min(data), max(data))

        if not isinstance(self.view.camera, scene.PanZoomCamera):
            raise ValueError("Camera of unexpected type.")

        if self.x_range is None or self.y_range is None:
            self.view.camera.rect = xyxy2xywh(*x_range, *y_range)
            self.x_range = x_range
            self.y_range = y_range
        else:
            x_percentage_difference = perc_diff(self.x_range, x_range)
            y_percentage_difference = perc_diff(self.y_range, y_range)
            if x_percentage_difference > 0.5:
                self.x_range = x_range
                self.view.camera.rect = xyxy2xywh(*x_range, *y_range)
            if y_percentage_difference > 0.5:
                self.y_range = y_range
                self.view.camera.rect = xyxy2xywh(*self.x_range, *self.y_range)


def xyxy2xywh(x_min, x_max, y_min, y_max):
    w = x_max - x_min
    # x = (x_min + x_max) / 2
    h = y_max - y_min
    # y = (y_min + y_max) / 2
    return (x_min, y_min, w, h)


def diff(x, y):
    return sum([abs(i - j) for i, j in zip(x, y)])


def avg(x, y):
    return sum([abs(i + j) for i, j in zip(x, y)]) / 2


def perc_diff(x, y):
    return diff(x, y) / avg(x, y)
