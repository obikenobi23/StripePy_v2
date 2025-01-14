#!/usr/bin/env python3

# Copyright (C) 2024 Andrea Raffo <andrea.raffo@ibv.uio.no>
#
# SPDX-License-Identifier: MIT

import argparse
import itertools
import pathlib
import subprocess as sp
import time


# Create a custom formatter to allow multiline and bulleted descriptions
class CustomFormatter(argparse.RawTextHelpFormatter):
    def _fill_text(self, text, width, indent):
        return "".join([indent + line + "\n" for line in text.splitlines()])


def _input_dir_checked(arg: str) -> pathlib.Path:
    input_dir = pathlib.Path(arg)
    if input_dir.exists() and input_dir.is_dir():
        return pathlib.Path(arg)

    raise FileNotFoundError(f'Input folder "{arg}" is not reachable: folder does not exist')


def _output_dir_checked(arg: str) -> pathlib.Path:
    parent = pathlib.Path(arg).parent
    if parent.exists() and parent.is_dir():
        return pathlib.Path(arg)

    raise FileNotFoundError(f'Output folder "{arg}" is not reachable: parent folder does not exist')


def _probability(arg) -> float:
    if 0 <= (n := float(arg)) <= 1:
        return n

    raise ValueError("Not a valid probability")


def make_cli():
    cli = argparse.ArgumentParser(
        description="This script runs StripePy over StripeBench, a benchmark containing 64 simulated Hi-C contact maps generated "
        "via the computational tool MoDLE at different resolutions, contact densities and noise levels.",
        formatter_class=CustomFormatter,
    )

    cli.add_argument(
        "stripepy-exec",
        type=pathlib.Path,
        help="Path to StripePy executable",
    )

    cli.add_argument(
        "stripebench-path",
        type=_input_dir_checked,
        help="Path to the StripeBench dataset, which can be downloaded from XX.",
        # TODO complete when benchmark is online
    )

    cli.add_argument(
        "-b",
        "--genomic-belt",
        type=int,
        default=5_000_000,
        help="Radius of the band, centred around the diagonal, where the search is restricted to "
        "(in bp). The value used for the StripeBench benchmark is here set as default.",
    )

    cli.add_argument(
        "-o",
        "--output-folder",
        type=_output_dir_checked,
        default=pathlib.Path.cwd(),
        help="Path to the folder where the user wants the output to be placed (default: current folder).",
    )

    cli.add_argument(
        "--max-width",
        type=int,
        default=20_000,
        help="Maximum stripe width, in bp.",
    )

    cli.add_argument(
        "--glob-pers-min",
        type=_probability,
        default=0.05,
        help="Threshold value between 0 and 1 to filter persistence maxima points and identify loci of interest, "
        "aka seeds. The value used for the StripeBench benchmark is here set as default.",
    )

    cli.add_argument(
        "--loc-pers-min",
        type=_probability,
        default=0.25,
        help="Threshold value between 0 and 1 to find peaks in signal in a horizontal domain while estimating the "
        "height of a stripe. The value used for the StripeBench benchmark is here set as default.",
    )

    cli.add_argument(
        "--loc-trend-min",
        type=_probability,
        default=0.05,
        help="Threshold value between 0 and 1 to estimate the height of a stripe; the higher this value, the shorter "
        "the stripe; it is always used when --constrain-heights is set to 'False', but could be necessary also "
        "when --constrain-heights is 'True' and no persistent maximum other than the global maximum is found. "
        "The value used for the StripeBench benchmark is here set as default.",
    )

    cli.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing file(s).",
    )

    return cli


def run_stripepy(
    stripepy_exec,
    path_to_mcool,
    resolution,
    genomic_belt,
    output_folder,
    max_width,
    glob_pers_min,
    loc_pers_min,
    loc_trend_min,
    force,
):
    args = [
        stripepy_exec,
        "call",
        path_to_mcool,
        resolution,
        "-b",
        str(genomic_belt),
        "--output-file",
        str(output_folder / path_to_mcool.stem / str(resolution) / "results.hdf5"),
        "--max-width",
        str(max_width),
        "--glob-pers-min",
        str(glob_pers_min),
        "--loc-pers-min",
        str(loc_pers_min),
        "--loc-trend-min",
        str(loc_trend_min),
    ]

    if force:
        args.append("--force")

    try:
        sp.check_call(args)
    except sp.CalledProcessError as e:
        if "unrecognized arguments: --output-file" not in e:
            raise
        i = args.index("--output-file")
        args[i] = "--output-folder"
        args[i + i] = output_folder
        sp.check_call(args)


def main():
    args = vars(make_cli().parse_args())

    with open(args["output_folder"] / "output.log", "w") as f:
        t0 = time.time()
        resolutions = ("5000", "10000", "25000", "50000")
        contact_densities = ("1", "5", "10", "15")
        noise_levels = ("0", "5000", "10000", "15000")

        params = itertools.product(contact_densities, noise_levels, resolutions)
        for contact_density, noise_level, resolution in params:
            this_contact_map = (
                args["stripebench-path"]
                / "data"
                / f"grch38_h1_rad21_{contact_density}_{noise_level}"
                / f"grch38_h1_rad21_{contact_density}_{noise_level}.mcool"
            )
            run_stripepy(
                args["stripepy-exec"],
                this_contact_map,
                resolution,
                args["genomic_belt"],
                args["output_folder"],
                args["max_width"],
                args["glob_pers_min"],
                args["loc_pers_min"],
                args["loc_trend_min"],
                args["force"],
            )
        delta = time.time() - t0
        print("Total time: ", file=f)
        print(delta, file=f)


if __name__ == "__main__":
    main()
