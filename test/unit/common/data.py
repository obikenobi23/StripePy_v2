# Copyright (C) 2024 Roberto Rossini <roberros@uio.no>
#
# SPDX-License-Identifier: MIT

import functools
from typing import Dict


@functools.cache
def generate_chromosomes() -> Dict[str, int]:
    return {
        "chr2L": 23513712,
        "chr2R": 25286936,
        "chr3L": 28110227,
        "chr3R": 32079331,
        "chr4": 1348131,
        "chrX": 23542271,
        "chrY": 3667352,
        "chrM": 19524,
    }
