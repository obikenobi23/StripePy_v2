import numpy as np


def colorbar(matrix):
    find_normal_values = matrix[np.isfinite(matrix)]
    max_float = np.nanmax(find_normal_values)
    min_float = np.nanmin(find_normal_values)
    return _colorbar(max_float, min_float)


def _colorbar(max_float, min_float):
    tickvals = [exponent for exponent in range(int(min_float) - 1, int(max_float) + 1)]

    ticktext = [translate(val) for val in tickvals]

    return dict(
        title="Counts (log)",
        tickmode="array",
        exponentformat="e",
        tickvals=tickvals,
        ticktext=ticktext,
        separatethousands=True,
    )


def translate(exponent):
    exp_string = str(exponent)
    superscript_map = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "-": "⁻",
    }

    superscript_string = "10"
    for digit in exp_string:
        superscript_string += superscript_map[digit]
    return superscript_string
