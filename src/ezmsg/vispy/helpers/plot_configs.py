import enum
from typing import Optional
from typing import Union

import ezmsg.core as ez
from vispy import color as vispy_color


class PlotType(enum.Enum):
    HISTOGRAM = enum.auto()
    IMAGE = enum.auto()
    PLOT = enum.auto()
    SPECTROGRAM = enum.auto()
    VOLUME = enum.auto()
    SURFACE = enum.auto()


class PlotSettings(ez.Settings):
    ...


class HistogramSettings(PlotSettings):
    bins: int = 10
    color: Union[vispy_color.Color, str] = "w"
    orientation: str = "h"


class ImageSettings(PlotSettings):
    cmap: str = "cubehelix"
    clim: Union[str, tuple] = "auto"
    fg_color: Optional[vispy_color.Color] = None


class LineSettings(PlotSettings):
    color: Union[vispy_color.Color, str] = "k"
    symbol: str = None
    line_kind: str = "-"
    width: float = 1.0
    marker_size: float = 10.0
    edge_color: Union[vispy_color.Color, str] = "k"
    face_color: Union[vispy_color.Color, str] = "b"
    edge_width: float = 1.0
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    connect: Optional[str] = "strip"


class MultiLineSettings(PlotSettings):
    color: Union[vispy_color.Color, str] = "k"
    symbol: str = None
    line_kind: str = "-"
    width: float = 1.0
    marker_size: float = 10.0
    edge_color: Union[vispy_color.Color, str] = "k"
    face_color: Union[vispy_color.Color, str] = "b"
    edge_width: float = 1.0
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    connect: Optional[str] = "strip"


class SpectrogramSettings(PlotSettings):
    n_fft: int = 256
    step: Optional[int] = None
    fs: float = 1.0
    window: Optional[str] = "hann"
    normalize: bool = False
    color_scale: str = "log"
    cmap: str = "cubehelix"
    clim: Union[str, tuple] = "auto"


class VolumeSettings(PlotSettings):
    clim: tuple[float, float] = None
    method: str = "mip"
    threshold: float = None
    cmap: str = "grays"


class SurfaceSettings(PlotSettings):
    ...


class RollingSpectrogramSettings(PlotSettings):
    fs: float = None
    window_length_n: float = None
    window_length_t: float = None
    dt: float = None
    dy: float = None
    normalize: bool = False
    color_scale: str = "log"
    cmap: str = "cubehelix"
    clim: Union[str, tuple] = "auto"
