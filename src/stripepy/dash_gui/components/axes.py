import math


def compute_x_axis_range(chromosome_name, htk_object, resolution, desired_magnitude):
    magnitude_decision = {
        "Kb": 10**3,
        "Mb": 10**6,
        "Gb": 10**9,
    }
    magnitude_number = magnitude_decision[desired_magnitude]

    if chromosome_name:  # XX:Y,000-Z,000
        _, _, spans = chromosome_name.partition(":")
        pre_span = 0
        for chrom_names, pre_span_lengths in htk_object.chromosomes().items():
            if chrom_names == chromosome_name:
                span_end = pre_span + pre_span_lengths
                break
            else:
                pre_span += pre_span_lengths
        if spans:
            span_start, _, span_end = spans.partition("-")
            span_start = int(span_start.replace(",", ""))
            span_end = int(span_end.replace(",", ""))
        else:
            span_start = pre_span
    else:  # No input means read the entire matrix
        span_start = 0
        span_end = htk_object.nbins() * resolution

    tickvals = [(bins) / resolution for bins in range(0, span_end - span_start, magnitude_number)]

    span_start_bp = math.ceil(span_start / magnitude_number)
    span_end_bp = math.floor(span_end / magnitude_number)
    ticktext = [str(bps + span_start_bp) + desired_magnitude for bps in range(0, span_end_bp - span_start_bp, 1)]

    bin_number = (span_end - span_start) / resolution + 1
    if len(tickvals) > 15:
        tickvals = _trim_list(tickvals)
        ticktext = _trim_list(ticktext)
    elif len(tickvals) > bin_number:
        tickvals = _trim_list(tickvals, bin_number)
        ticktext = _trim_list(ticktext, bin_number)
    return tickvals, ticktext


def compute_x_axis_chroms(htk_object):
    chromosomes = htk_object.chromosomes()

    tickvals = []
    ticktext = []
    span_sum = 0
    for chromosome_name, chromosome_length in chromosomes.items():
        span_sum += chromosome_length
        tickvals.append(span_sum / htk_object.resolution())
        ticktext.append(chromosome_name)

    return tickvals, ticktext


def _trim_list(list_long, max_number=15):
    original_length = len(list_long)

    num_elements_to_pick = max_number - 1
    step_size = math.ceil(original_length / num_elements_to_pick)

    trimmed_list = []
    for i in range(0, original_length, step_size):
        trimmed_list.append(list_long[i])
    trimmed_list.append(list_long[-1])
    return trimmed_list
