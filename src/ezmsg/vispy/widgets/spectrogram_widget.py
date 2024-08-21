from typing import Optional
from typing import Union

import numpy as np

from vispy import scene

from ..helpers.ranged_pan_zoom import RangedPanZoomCamera
from .plot_widget import BasePlotWidget


class SpectrogramWidget(BasePlotWidget):
    """
    Calculate and show a spectrogram

    Parameters
    ----------
    x : array-like
        1D signal to operate on. ``If len(x) < n_fft``, x will be
        zero-padded to length ``n_fft``.
    n_fft : int
        Number of FFT points. Much faster for powers of two.
    step : int | None
        Step size between calculations. If None, ``n_fft // 2``
        will be used.
    fs : float
        The sample rate of the data.
    window : str | None
        Window function to use. Can be ``'hann'`` for Hann window, or None
        for no windowing.
    normalize : bool
        Normalization of spectrogram values across frequencies.
    color_scale : {'linear', 'log'}
        Scale to apply to the result of the STFT.
        ``'log'`` will use ``10 * log10(power)``.
    cmap : str
        Colormap name.
    clim : str | tuple
        Colormap limits. Should be ``'auto'`` or a two-element tuple of
        min and max values.
    *args : list
        Positional arguments to pass to `BasePlotWidget`.
    **kwargs : dict
        Keyword arguments to pass to `BasePlotWidget`.
    """

    def __init__(
        self,
        x=None,
        n_fft=256,
        step=None,
        fs=1.0,
        window="hann",
        normalize=False,
        color_scale="log",
        cmap="cubehelix",
        clim="auto",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._configure_2d()
        self.view.camera = RangedPanZoomCamera(aspect=1)
        self._spec = scene.Spectrogram(
            x,
            n_fft,
            step,
            fs,
            window,
            normalize,
            color_scale,
            cmap,
            clim,
            parent=self.view.scene,  # type: ignore
        )
        self.link_views()

    def update(
        self,
        data: Optional[np.ndarray] = None,
        clim: Optional[Union[tuple[float, float], str]] = None,
        cmap: Optional[str] = None,
    ):
        """
        Update the spectrogram

        Parameters
        ----------
        data: np.ndarray
            1D signal to operate on. ``If len(x) < n_fft``, data will be
            zero-padded to length ``n_fft``.
        cmap : str
            Colormap name.
        clim : str | tuple
            Colormap limits. Should be ``'auto'`` or a two-element tuple of
            min and max values.
        """
        if isinstance(data, np.ndarray):
            self._spec.x = data
        if isinstance(clim, tuple):
            self._spec.clim = clim
            self._clim_auto = False
        elif isinstance(clim, str) and clim == "auto":
            self._clim_auto = True
        if isinstance(cmap, str):
            self._spec.cmap = cmap
        if self._clim_auto is True:
            self._spec.clim = "auto"
