# Copyright (C) 2025 Bendik Berg <bendber@ifi.uio.no>
#
# SPDX-License-Identifier: MIT

import hictkpy
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
from HiCObject import HiCObject

import stripepy

app = Dash(__name__)

hictk_reader = HiCObject()


app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            style={"width": "90vh", "height": "90vh"},
                            id="HeatMap",
                        ),
                    ],
                    style={"display": "inline-block"},
                ),
                html.Div(
                    [  # Right side of screen
                        html.Div(
                            [
                                dcc.Input(
                                    placeholder="File path",
                                    type="text",
                                    value="",
                                    id="file-path",
                                    style={"width": 300, "fontSize": 20},
                                ),
                                dcc.Input(
                                    placeholder="Resolution",
                                    type="number",
                                    value="",
                                    id="resolution",
                                    style={"width": 300, "fontSize": 20},
                                ),
                                html.Button(id="submit-file", n_clicks=0, children="Submit"),
                            ],
                            style={"paddingBottom": 100},
                        ),
                        html.Div(
                            [
                                dcc.Input(
                                    placeholder="Chromosome name",
                                    type="text",
                                    value="",
                                    id="chromosome-name",
                                    disabled=True,
                                    style={"width": 300, "fontSize": 20},
                                ),
                                dcc.Input(
                                    placeholder="Chromosome interval",
                                    type="text",
                                    value="",
                                    id="chromosome-interval",
                                    disabled=True,
                                    style={"width": 300, "fontSize": 20},
                                ),
                                dcc.Input(
                                    placeholder="Color map",
                                    type="text",
                                    value="",
                                    id="color-map",
                                    disabled=True,
                                    style={"width": 300, "fontSize": 20},
                                ),
                                html.Button(
                                    n_clicks=0,
                                    children="Submit",
                                    id="submit-chromosome",
                                    disabled=True,
                                ),
                            ],
                            style={"paddingBottom": 60},
                        ),
                        dcc.Dropdown(
                            options=["KR", "VC", "VC_SQRT"],
                            placeholder="Normalization",
                            value="KR",
                            id="normalization",
                        ),
                        html.Div(
                            [
                                "minimum top persistence ",
                                dcc.Input(
                                    type="number",
                                    value="0.5",
                                    id="top-pers-input",
                                    style={"width": 300},
                                ),
                            ],
                            style={"marginTop": 40},
                        ),
                        html.Div(
                            [
                                "relative change ",
                                dcc.Input(
                                    type="number",
                                    value="0.5",
                                    id="rel-change-input",
                                    style={"width": 300},
                                ),
                            ],
                            style={"marginTop": 40},
                        ),
                        html.Div(
                            [
                                "genomic belt ",
                                dcc.Input(
                                    type="number",
                                    value="1000000",
                                    id="gen-belt-input",
                                    style={"width": 300},
                                ),
                            ],
                            style={"marginTop": 40},
                        ),
                        html.Div(
                            [
                                "loc trend min ",
                                dcc.Input(
                                    type="number",
                                    value="0.5",
                                    id="loc-trend-input",
                                    style={"width": 300},
                                ),
                            ],
                            style={"marginTop": 40},
                        ),
                        html.Div(
                            [
                                "stripe type ",
                                dcc.Input(
                                    type="number",
                                    value="0.5",
                                    id="stripe-type-input",
                                    style={"width": 300},
                                ),
                            ],
                            style={"marginTop": 40},
                        ),
                    ],
                    style={"marginTop": 95},
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(id="meta-info"),
        html.Div(id="callbacks-file", style={"display": "none"}),
    ]
)


@app.callback(
    Output("meta-info", "children"),
    # Output("callbacks-file", "children"),
    Output("chromosome-name", "disabled"),
    Output("chromosome-interval", "disabled"),
    Output("color-map", "disabled"),
    Output("submit-chromosome", "disabled"),
    Input("submit-file", "n_clicks"),
    State("file-path", "value"),
    State("resolution", "value"),
    prevent_initial_call=True,
    running=[(Output("submit-file", "disabled"), True, False)],
)
def update_file(n_clicks, filename, resolution):

    hictk_reader.path = filename
    hictk_reader.resolution = resolution

    metaInfo_attributes = html.Div(
        [html.P((attribute, ": ", str(value))) for attribute, value in hictk_reader.attributes.items()]
    )
    metaInfo_nnz = html.P(("Non-zero values: ", str(hictk_reader.nnz)))
    metaInfo_chromosomes = html.Div(
        [html.P((chromosome, ":", name)) for chromosome, name in hictk_reader._chromosomes.items()]
    )

    metaInfo = html.Div([html.Div([metaInfo_attributes]), html.Div([metaInfo_nnz]), html.Div([metaInfo_chromosomes])])

    return metaInfo, False, False, False, False


@app.callback(
    Output("HeatMap", "figure"),
    # Output(chosenChromosome),
    Input("submit-chromosome", "n_clicks"),
    State("chromosome-name", "value"),
    State("chromosome-interval", "value"),
    State("normalization", "value"),
    # State("color-maps", "value"),
    prevent_initial_call=True,
    running=[(Output("submit-chromosome", "disabled"), True, False)],
)
def update_plot(
    n_clicks,
    chromosome_name,
    chromosome_interval,
    normalization,
):

    hictk_reader.region_of_interest = chromosome_name + ":" + chromosome_interval
    hictk_reader.normalization = normalization

    frame = hictk_reader.selector

    fig = go.Figure(data=go.Heatmap(z=np.where(frame > 0, np.log10(frame), 0)))
    fig.update_yaxes(autorange="reversed")

    return fig


import webbrowser

# webbrowser.open("http://127.0.0.1:8050/")

if __name__ == "__main__":
    app.run_server(debug=True)
