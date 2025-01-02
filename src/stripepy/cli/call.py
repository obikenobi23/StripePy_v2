# Copyright (C) 2024 Andrea Raffo <andrea.raffo@ibv.uio.no>
#
# SPDX-License-Identifier: MIT

import contextlib
import multiprocessing as mp
import time
from typing import Any, Dict

import numpy as np

from stripepy import IO, others, stripepy


def _generate_metadata_attribute(configs_input: Dict[str, Any], configs_thresholds: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "constrain-heights": configs_thresholds["constrain_heights"],
        "genomic-belt": configs_input["genomic_belt"],
        "global-persistence-minimum": configs_thresholds["glob_pers_min"],
        "local-persistence-minimum": configs_thresholds["loc_pers_min"],
        "local-trend-minimum": configs_thresholds["loc_trend_min"],
        "max-width": configs_thresholds["max_width"],
        "min-chromosome-size": configs_thresholds["min_chrom_size"],
    }


def run(
    configs_input: Dict[str, Any],
    configs_thresholds: Dict[str, Any],
    configs_output: Dict[str, Any],
    configs_other: Dict[str, Any],
):
    # How long does stripepy take to analyze the whole Hi-C matrix?
    start_global_time = time.time()

    # Data loading:
    f, chr_starts, chr_ends, bp_lengths = others.cmap_loading(configs_input["contact_map"], configs_input["resolution"])

    # Remove existing folders:
    # configs_output["output_folder"] = (
    #     f"{configs_output['output_folder']}/{configs_input['contact_map'].stem}/{configs_input['resolution']}"
    # )
    configs_output["output_folder"] = (
        configs_output["output_folder"] / configs_input["contact_map"].stem / str(configs_input["resolution"])
    )
    IO.remove_and_create_folder(configs_output["output_folder"], configs_output["force"])

    # Extract a list of tuples where each tuple is (index, chr), e.g. (2,'chr3'):
    c_pairs = others.chromosomes_to_study(
        list(f.chromosomes().keys()), bp_lengths, configs_thresholds["min_chrom_size"]
    )

    with contextlib.ExitStack() as ctx:
        # Create HDF5 file to store candidate stripes:
        h5 = ctx.enter_context(IO.ResultFile(configs_output["output_folder"] / "results.hdf5", "w"))

        h5.init_file(f, configs_input["normalization"], _generate_metadata_attribute(configs_input, configs_thresholds))

        # Set up the process pool when appropriate
        if configs_other["nproc"] > 1:
            pool = ctx.enter_context(mp.Pool(configs_other["nproc"]))
        else:
            pool = None

        # Lopping over all chromosomes:
        for this_chr_idx, this_chr in c_pairs:

            print(f"\n{IO.ANSI.RED}CHROMOSOME {this_chr}{IO.ANSI.ENDC}")
            start_local_time = time.time()

            # Removing and creating folders to store output files:
            # configs_input['roi'] = None
            if configs_input["roi"] is not None:
                IO.create_folders_for_plots(configs_output["output_folder"] / "plots" / this_chr)

            I = f.fetch(this_chr, normalization=configs_input["normalization"]).to_csr("full")

            # RoI:
            RoI = others.define_RoI(
                configs_input["roi"], chr_starts[this_chr_idx], chr_ends[this_chr_idx], configs_input["resolution"]
            )
            print(f"RoI is: {RoI}")

            print(f"{IO.ANSI.YELLOW}Step 1: pre-processing step{IO.ANSI.ENDC}")
            start_time = time.time()
            LT_Iproc, UT_Iproc, Iproc_RoI = stripepy.step_1(
                I,
                configs_input["genomic_belt"],
                configs_input["resolution"],
                RoI=RoI,
            )
            print(f"Execution time of step 1: {time.time() - start_time} seconds ---")

            # Find the indices where the sum is zero
            # TODO: DO SOMETHING
            # zero_indices = np.where(np.sum(Iproc_RoI, axis=0) == 0)[0]
            # print(np.min(np.sum(LT_Iproc + UT_Iproc, axis=0)))
            # print(np.max(np.sum(LT_Iproc + UT_Iproc, axis=0)))
            # np.savetxt("trend.txt", np.sum(LT_Iproc + UT_Iproc, axis=0))
            # exit()

            print(f"{IO.ANSI.YELLOW}Step 2: Topological Data Analysis{IO.ANSI.ENDC}")
            start_time = time.time()

            result = stripepy.step_2(
                this_chr,
                f.chromosomes().get(this_chr),
                LT_Iproc,
                UT_Iproc,
                configs_thresholds["glob_pers_min"],
            )
            print(f"Execution time of step 2: {time.time() - start_time} seconds ---")

            if RoI is not None:
                result.set_roi(RoI)

            print(f"{IO.ANSI.YELLOW}Step 3: Shape analysis{IO.ANSI.ENDC}")
            start_time = time.time()

            result = stripepy.step_3(
                result,
                LT_Iproc,
                UT_Iproc,
                configs_input["resolution"],
                configs_input["genomic_belt"],
                configs_thresholds["max_width"],
                configs_thresholds["loc_pers_min"],
                configs_thresholds["loc_trend_min"],
                map=pool.map if pool is not None else map,
            )
            print(f"Execution time of step 3: {time.time() - start_time} seconds ---")

            print(f"{IO.ANSI.YELLOW}Step 4: Statistical analysis and post-processing{IO.ANSI.ENDC}")
            start_time = time.time()

            result = stripepy.step_4(
                result,
                LT_Iproc,
                UT_Iproc,
            )

            print(f"Execution time of step 4: {time.time() - start_time} seconds ---")

            if result.roi is not None:
                start_time = time.time()
                print(f"{IO.ANSI.YELLOW}Step 5: Generating plots{IO.ANSI.ENDC}")
                stripepy.step_5(
                    result,
                    configs_input["resolution"],
                    LT_Iproc,
                    UT_Iproc,
                    f.fetch(
                        f"{this_chr}:{result.roi['genomic'][0]}-{result.roi['genomic'][1]}",
                        normalization=configs_input["normalization"],
                    ).to_numpy("full"),
                    Iproc_RoI,
                    configs_input["genomic_belt"],
                    configs_thresholds["loc_pers_min"],
                    configs_thresholds["loc_trend_min"],
                    configs_output["output_folder"] / "plots",
                    map=pool.map if pool is not None else map,
                )

                print(f"Execution time of step 5: {time.time() - start_time} seconds ---")

            print(f'Writing results for "{this_chr}" to file "{h5.path}"...')
            h5.write_descriptors(result)

            print(f"{IO.ANSI.CYAN}This chromosome has taken {(time.time() - start_local_time)} seconds{IO.ANSI.ENDC}")

    print(f"\n\n{IO.ANSI.RED}The code has run for {(time.time() - start_global_time) / 60} minutes{IO.ANSI.ENDC}")
