import logging
from typing import Optional

import numpy as np

from vispy import scene
from vispy.geometry import Rect

logger = logging.getLogger(__name__)


class RangedPanZoomCamera(scene.PanZoomCamera):
    """TODO: Update documentation.

    Long description here.

    Parameters
    ----------
    name : type
        description

    **kwargs : dict
        Keyword arguments to pass to `PanZoomCamera`.

    Notes
    -----
    Interaction:

        * LMB: pan the view
        * RMB or scroll: zooms the view

    """

    def __init__(
        self,
        horizontal_zoom=True,
        vertical_zoom=True,
        vert_pan=True,
        vert_center=False,
        **kwargs
    ):
        self._limits = None
        self._vert_center = vert_center
        self._vert_zoom = vertical_zoom
        self._horz_zoom = horizontal_zoom
        self._vert_pan = vert_pan
        super().__init__(**kwargs)

    @property
    def limits(self):
        return self._limits

    @limits.setter
    def limits(self, args):
        if isinstance(args, tuple):
            rect = Rect(*args)
        else:
            rect = Rect(args)

        if self._limits != rect:
            self._limits = rect

    @scene.PanZoomCamera.rect.setter
    def rect(self, args):
        if isinstance(args, tuple):
            rect = Rect(*args)
        else:
            rect = Rect(args)

        if self._limits is not None:
            new_area = rect.height * rect.width
            if self._rect is not None:
                current_area = self.rect.height * self.rect.width
            else:
                current_area = new_area
            # This is a fix to allow zooming out if at the limit,
            # but prevents zooming in caused from panning.
            if new_area > current_area:
                if rect.left < self._limits.left:
                    rect.left = self._limits.left
                if rect.right > self._limits.right:
                    rect.right = self._limits.right
                if rect.top > self._limits.top:
                    rect.top = self._limits.top
                if rect.bottom < self._limits.bottom:
                    rect.bottom = self._limits.bottom
            elif (
                rect.left < self._limits.left
                or rect.right > self._limits.right
                or rect.top > self._limits.top
                or rect.bottom < self._limits.bottom
            ):
                return

        if self._rect != rect:
            self._rect = rect
            self.view_changed()

    def pan(self, *pan):
        """Pan the view.

        Parameters
        ----------
        *pan : length-2 sequence
            The distance to pan the view, in the coordinate system of the
            scene.
        """
        if len(pan) == 1:
            pan = pan[0]
        if self._vert_pan is False:
            pan[1] = 0.0
        self.rect = self.rect + pan

    def zoom(self, factor, center=None, override=False):
        """Zoom in (or out) at the given center

        Parameters
        ----------
        factor : float or tuple
            Fraction by which the scene should be zoomed (e.g. a factor of 2
            causes the scene to appear twice as large).
        center : tuple of 2-4 elements
            The center of the view. If not given or None, use the
            current center.
        """
        # Init some variables
        center = center if (center is not None) else self.center
        assert len(center) in (2, 3, 4)
        # Get scale factor, take scale ratio into account
        if np.isscalar(factor):
            scale = [factor, factor]
        else:
            if len(factor) != 2:
                raise TypeError("factor must be scalar or length-2 sequence.")
            scale = list(factor)
        if self.aspect is not None:
            scale[0] = scale[1]

        # Make a new object (copy), so that allocation will
        # trigger view_changed:
        rect = Rect(self.rect)
        # Get space from given center to edges and scale these spaces
        if self._vert_zoom is True or override is True:
            bottom_space = center[1] - rect.bottom
            rect.bottom = center[1] - bottom_space * scale[1]
            top_space = rect.top - center[1]
            rect.top = center[1] + top_space * scale[1]
        if self._horz_zoom is True or override is True:
            left_space = center[0] - rect.left
            rect.left = center[0] - left_space * scale[0]
            right_space = rect.right - center[0]
            rect.right = center[0] + right_space * scale[0]
        self.rect = rect

    def viewbox_mouse_event(self, event):
        """
        The SubScene received a mouse event; update transform
        accordingly.

        Parameters
        ----------
        event : instance of Event
            The event.
        """
        if event.handled or not self.interactive:
            return

        if event.type == "mouse_move":
            if event.press_event is None:
                return

            modifiers = event.mouse_event.modifiers

            if 2 in event.buttons and not modifiers:
                # Zoom
                p1c = np.array(event.last_event.pos)[:2]
                p2c = np.array(event.pos)[:2]
                if self._vert_zoom is False:
                    p1c[0] = 0
                    p2c[0] = 0
                    if self._vert_center is True:
                        center = self._transform.imap(event.press_event.pos[:2])
                    else:
                        center = self._rect.center
                elif self._horz_zoom is False:
                    p1c[1] = 0
                    p2c[1] = 0
                    center = self._transform.imap(event.press_event.pos[:2])
                else:
                    center = self._transform.imap(event.press_event.pos[:2])
                scale = (1 + self.zoom_factor) ** ((p1c - p2c) * np.array([1, -1]))
                self.zoom(scale, center, override=True)
                event.handled = True
            else:
                event.handled = False
        else:
            event.handled = False

        super().viewbox_mouse_event(event)

    def move_to_edge(self, val: float, side: Optional[str] = None):
        if side is None:
            assert "Must provide left,right to align camera"
        rect = Rect(self.rect)
        width = rect.width
        if side == "left":
            rect.left = val
            rect.right = val + width
        elif side == "right":
            rect.right = val
            rect.left = val - width
        self.rect = rect
