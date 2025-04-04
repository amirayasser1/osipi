import warnings

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from ._convolution import exp_conv


def tofts(
    t: NDArray[np.floating],
    ca: NDArray[np.floating],
    Ktrans: np.floating,
    ve: np.floating,
    Ta: np.floating = 30.0,
    discretization_method: str = "conv",
) -> NDArray[np.floating]:
    """Tofts model as defined by Tofts and Kermode (1991)

    Args:
        t (NDArray[np.floating]): array of time points in units of sec. [OSIPI code Q.GE1.004]
        ca (NDArray[np.floating]):
            Arterial concentrations in mM for each time point in t. [OSIPI code Q.IC1.001]
        Ktrans (np.floating):
            Volume transfer constant in units of 1/min. [OSIPI code Q.PH1.008]
        ve (np.floating):
            Relative volume fraction of the extracellular
            extravascular compartment (e). [OSIPI code Q.PH1.001.[e]]
        Ta (np.floating, optional):
            Arterial delay time,
            i.e., difference in onset time between tissue curve and AIF in units of sec. Defaults to 30 seconds. [OSIPI code Q.PH1.007]
        discretization_method (str, optional): Defines the discretization method. Options include

            – 'conv': Numerical convolution (default) [OSIPI code G.DI1.001]

            – 'exp': Exponential convolution [OSIPI code G.DI1.006]


    Returns:
        NDArray[np.floating]: Tissue concentrations in mM for each time point in t.

    See Also:
        `extended_tofts`

    References:
        - Lexicon url:
            https://osipi.github.io/OSIPI_CAPLEX/perfusionModels/#indicator-kinetic-models
        - Lexicon code: M.IC1.004
        - OSIPI name: Tofts Model
        - Adapted from contributions by: LEK_UoEdinburgh_UK, ST_USyd_AUS, MJT_UoEdinburgh_UK

    Example:

        Create an array of time points covering 6 min in steps of 1 sec,
        calculate the Parker AIF at these time points, calculate tissue concentrations
        using the Tofts model and plot the results.

        Import packages:

        >>> import matplotlib.pyplot as plt
        >>> import osipi
        >>> import numpy

        Calculate AIF:

        >>> t = np.arange(0, 6 * 60, 1)
        >>> ca = osipi.aif_parker(t)

        Calculate tissue concentrations and plot:

        >>> Ktrans = 0.6  # in units of 1/min
        >>> ve = 0.2  # takes values from 0 to 1
        >>> ct = osipi.tofts(t, ca, Ktrans, ve)
        >>> plt.plot(t, ca, "r", t, ct, "b")

    """
    if not np.allclose(np.diff(t), np.diff(t)[0]):
        warnings.warn(
            ("Non-uniform time spacing detected. Time array may be" " resampled."),
            stacklevel=2,
        )

    if Ktrans <= 0 or ve <= 0:
        ct = 0 * ca

    else:
        # Convert units
        Ktrans = Ktrans / 60  # from 1/min to 1/sec

        if discretization_method == "exp":  # Use exponential convolution
            # Shift the AIF by the arterial delay time (if not zero)
            if Ta != 0:
                f = interp1d(
                    t,
                    ca,
                    kind="linear",
                    bounds_error=False,
                    fill_value=0,
                )
                ca = (t > Ta) * f(t - Ta)

            Tc = ve / Ktrans
            ct = ve * exp_conv(Tc, t, ca)

        else:  # Use convolution by default
            # Calculate the impulse response function
            kep = Ktrans / ve
            imp = Ktrans * np.exp(-1 * kep * t)

            # Shift the AIF by the arterial delay time (if not zero)
            if Ta != 0:
                f = interp1d(
                    t,
                    ca,
                    kind="linear",
                    bounds_error=False,
                    fill_value=0,
                )
                ca = (t > Ta) * f(t - Ta)

            # Check if time data grid is uniformly spaced
            if np.allclose(np.diff(t), np.diff(t)[0]):
                # Convolve impulse response with AIF
                convolution = np.convolve(ca, imp)

                # Discard unwanted points and make sure time spacing
                # is correct
                ct = convolution[0 : len(t)] * t[1]
            else:
                # Resample at the smallest spacing
                dt = np.min(np.diff(t))
                t_resampled = np.linspace(t[0], t[-1], int((t[-1] - t[0]) / dt))
                ca_func = interp1d(
                    t,
                    ca,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                imp_func = interp1d(
                    t,
                    imp,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                ca_resampled = ca_func(t_resampled)
                imp_resampled = imp_func(t_resampled)
                # Convolve impulse response with AIF
                convolution = np.convolve(ca_resampled, imp_resampled)

                # Discard unwanted points and make sure time spacing
                # is correct
                ct_resampled = convolution[0 : len(t_resampled)] * t_resampled[1]

                # Restore time grid spacing
                ct_func = interp1d(
                    t_resampled,
                    ct_resampled,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                ct = ct_func(t)

    return ct


def extended_tofts(
    t: NDArray[np.floating],
    ca: NDArray[np.floating],
    Ktrans: np.floating,
    ve: np.floating,
    vp: np.floating,
    Ta: np.floating = 30.0,
    discretization_method: str = "conv",
) -> NDArray[np.floating]:
    """Extended tofts model as defined by Tofts (1997)

    Args:
        t (NDArray[np.floating]):
            array of time points in units of sec. [OSIPI code Q.GE1.004]
        ca (NDArray[np.floating]):
            Arterial concentrations in mM for each time point in t. [OSIPI code Q.IC1.001]
        Ktrans (np.floating):
            Volume transfer constant in units of 1/min. [OSIPI code Q.PH1.008]
        ve (np.floating):
            Relative volume fraction of the extracellular
            extravascular compartment (e). [OSIPI code Q.PH1.001.[e]]
        vp (np.floating):
            Relative volyme fraction of the plasma compartment (p). [OSIPI code Q.PH1.001.[p]]
        Ta (np.floating, optional):
            Arterial delay time, i.e., difference in onset time
            between tissue curve and AIF in units of sec.
            Defaults to 30 seconds. [OSIPI code Q.PH1.007]
        discretization_method (str, optional):
            Defines the discretization method. Options include

            – 'conv': Numerical convolution (default) [OSIPI code G.DI1.001]

            – 'exp': Exponential convolution [OSIPI code G.DI1.006]


    Returns:
        NDArray[np.floating]: Tissue concentrations in mM for each time point in t.

    See Also:
        `tofts`

    References:
        - Lexicon url: https://osipi.github.io/OSIPI_CAPLEX/perfusionModels/#indicator-kinetic-models
        - Lexicon code: M.IC1.005
        - OSIPI name: Extended Tofts Model
        - Adapted from contributions by: LEK_UoEdinburgh_UK, ST_USyd_AUS, MJT_UoEdinburgh_UK

    Example:

        Create an array of time points covering 6 min in steps of 1 sec,
        calculate the Parker AIF at these time points, calculate tissue concentrations
        using the Extended Tofts model and plot the results.

        Import packages:

        >>> import matplotlib.pyplot as plt
        >>> import osipi

        Calculate AIF

        >>> t = np.arange(0, 6 * 60, 0.1)
        >>> ca = osipi.aif_parker(t)

        Calculate tissue concentrations and plot

        >>> Ktrans = 0.6  # in units of 1/min
        >>> ve = 0.2  # takes values from 0 to 1
        >>> vp = 0.3  # takes values from 0 to 1
        >>> ct = osipi.extended_tofts(t, ca, Ktrans, ve, vp)
        >>> plt.plot(t, ca, "r", t, ct, "b")

    """

    if not np.allclose(np.diff(t), np.diff(t)[0]):
        warnings.warn(
            ("Non-uniform time spacing detected. Time array may be" " resampled."),
            stacklevel=2,
        )

    if Ktrans <= 0 or ve <= 0:
        ct = vp * ca

    else:
        # Convert units
        Ktrans = Ktrans / 60  # from 1/min to 1/sec

        if discretization_method == "exp":  # Use exponential convolution
            # Shift the AIF by the arterial delay time (if not zero)
            if Ta != 0:
                f = interp1d(
                    t,
                    ca,
                    kind="linear",
                    bounds_error=False,
                    fill_value=0,
                )
                ca = (t > Ta) * f(t - Ta)

            Tc = ve / Ktrans
            # expconv calculates convolution of ca and
            # (1/Tc)exp(-t/Tc), add vp*ca term for extended model
            ct = (vp * ca) + ve * exp_conv(Tc, t, ca)

        else:  # Use convolution by default
            # Calculate the impulse response function
            kep = Ktrans / ve
            imp = Ktrans * np.exp(-1 * kep * t)

            # Shift the AIF by the arterial delay time (if not zero)
            if Ta != 0:
                f = interp1d(
                    t,
                    ca,
                    kind="linear",
                    bounds_error=False,
                    fill_value=0,
                )
                ca = (t > Ta) * f(t - Ta)

            # Check if time data grid is uniformly spaced
            if np.allclose(np.diff(t), np.diff(t)[0]):
                # Convolve impulse response with AIF
                convolution = np.convolve(ca, imp)

                # Discard unwanted points, make sure time spacing is
                # correct and add vp*ca term for extended model
                ct = convolution[0 : len(t)] * t[1] + (vp * ca)
            else:
                # Resample at the smallest spacing
                dt = np.min(np.diff(t))
                t_resampled = np.linspace(t[0], t[-1], int((t[-1] - t[0]) / dt))
                ca_func = interp1d(
                    t,
                    ca,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                imp_func = interp1d(
                    t,
                    imp,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                ca_resampled = ca_func(t_resampled)
                imp_resampled = imp_func(t_resampled)
                # Convolve impulse response with AIF
                convolution = np.convolve(ca_resampled, imp_resampled)

                # Discard unwanted points, make sure time spacing is
                # correct and add vp*ca term for extended model
                ct_resampled = convolution[0 : len(t_resampled)] * t_resampled[1] + (
                    vp * ca_resampled
                )

                # Restore time grid spacing
                ct_func = interp1d(
                    t_resampled,
                    ct_resampled,
                    kind="quadratic",
                    bounds_error=False,
                    fill_value=0,
                )
                ct = ct_func(t)

    return ct
