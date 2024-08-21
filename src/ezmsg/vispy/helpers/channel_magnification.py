import numpy as np

from vispy.scene import transforms


class ChannelFocusTransform(transforms.BaseTransform):
    """Update documentation"""

    glsl_map = """
        vec4 mag_transform(vec4 pos) {
            float dist = pos.y - $center.y;
            if (dist == 0. || abs(dist) > $ch_width.y || $mag == 1) {
                return pos;
            }
            float dir = dist / abs(dist);

            if( abs(dist) < $ch_width.x ) {
                dist = dist * $mag;
            }
            else {
                dist = dir * $ch_width.y;
            }
            return vec4(pos.x, $center.y + dist, pos.z, pos.w);
        }"""

    glsl_imap = glsl_map

    def __init__(self, mag=3, ch_width=1, center=(0, 0)):
        self._center = center
        self._mag = mag
        self._ch_width = (ch_width, ch_width)
        super().__init__()

    @property
    def center(self):
        """The (x, y) center point of the transform."""
        return self._center

    @center.setter
    def center(self, center):
        if np.allclose(self._center, center):
            return
        self._center = center
        self.shader_map()
        self.shader_imap()

    @property
    def mag(self):
        """The scale factor used in the central region of the transform."""
        return self._mag

    @mag.setter
    def mag(self, mag):
        if self._mag == mag:
            return
        self._mag = mag
        self._trans = None
        self.shader_map()
        self.shader_imap()

    @property
    def ch_width(self):
        """The inner and outer radii of the circular area bounding the transform."""
        return self._ch_width

    @ch_width.setter
    def ch_width(self, ch_width):
        if np.allclose(self._ch_width, ch_width):
            return
        self._ch_width = (ch_width, ch_width)
        self._trans = None
        self.shader_map()
        self.shader_imap()

    def shader_map(self):
        fn = super().shader_map()
        fn["center"] = self._center  # uniform vec2
        fn["mag"] = float(self._mag)
        fn["ch_width"] = (self._ch_width[0] / float(self._mag), self._ch_width[1])
        return fn

    def shader_imap(self):
        fn = super().shader_imap()
        fn["center"] = self._center  # uniform vec2
        fn["mag"] = 1.0 / self._mag
        fn["ch_width"] = self._ch_width
        return fn
