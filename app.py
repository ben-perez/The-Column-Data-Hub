from datetime import datetime
import os
import base64
from urllib.parse import quote as urlquote
from typing import cast
from dash import Dash
import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import sqlite3

sqlite_path = "data.db"

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

numeric_columns_summary = [
                            "Clicks", 
                            "Sends", 
                            "Opens",
                            "Open Rate",
                            "Unsubscribes",
                            "Word Count",
                            "Click Rate",
                            "Link Count"
                          ]

numeric_columns_section = [
                            "Clicks", 
                            "LinkCount",
                            "SectionArticleLength"
                          ]

bar_data_scope_radio_items = dbc.RadioItems(
                                id="bar-scope-choice",
                                options = [ 
                                    {"label":"Article", "value":"whole"},
                                    {"label":"Section", "value":"section"}
                                ],
                                inline=False,
                                value = "section"
                            )

bar_data_type_radio_items = dbc.RadioItems(
                                id="bar-type-choice",
                                options = [ 
                                    {"label":"Sum", "value":"sum"},
                                    {"label":"Average", "value":"avg"}
                                ],
                                inline=False,
                                value = "avg"
                            )

bar_data_select_list = dbc.Select(
                        id="bar-data-choice",
                        size='md',
                        style={"width":"40%"}
                       )

trend_checklist = dbc.Checklist(
                            id="trend-data-choice",
                            options = [
                                {"label":"Clicks", "value":"Clicks"},
                                {"label":"Links", "value":"Link Count"},
                                {"label":"Sends", "value":"Sends"},
                                {"label":"Opens", "value":"Opens"},
                                {"label":"Unsubscribes", "value":"Unsubscribes"}#,
                                #{"label":"Clicks Per Link", "value":"ClicksToLinks"}
                            ],
                            value = ["Clicks", "Opens"],
                            labelStyle={'display': 'inline-block'}
                       )

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("The Column Data Hub", style={"text-align":"right", "justify-content":"right"}, class_name="col-md-2"),
            dbc.Row(
                [
                   dbc.Col(dcc.DatePickerRange(
                                id='date-picker-range',
                                min_date_allowed = '2020-07-20',
                                max_date_allowed = datetime.now(),
                                start_date = '2020-07-20',
                                end_date = datetime.now()
                         ),
                         width={"size":12, "offset":0}
                        )
                    ],
                  align="center"  
                ),
            dbc.Button("Upload Data", 
                       style={"justify-content":"right"}, 
                       id="upload-button", 
                       class_name="offset-md-6",
                       n_clicks=0),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ], 
        fluid=True),
    color="dark",
    dark=True
)

upload_modal = dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Upload New Data")),
                        dbc.ModalBody( 
                                    [
                                        dbc.Label("Upload click data files"),
                                        dcc.Upload(dbc.Button("Upload File"), id="file-upload", multiple=True),
                                        html.Ul(id="file-list"),
                                        html.Div(id="upload-success-label")
                                    ]
                        ),
                        dbc.ModalFooter(
                            [dbc.Button(
                                "Upload",
                                id="upload-files-button",
                                style={"justify-content":"left"},
                                n_clicks=0
                            ),
                             dbc.Button(
                                    "Close",
                                    id="close-modal",
                                    className="ms-auto",
                                    n_clicks=0
                                )
                            ]
                        ),
                    ],
                    id="upload-modal",
                    is_open=False,
                    scrollable=True
                )

body = dbc.Container(
      [ 
          dbc.Row(
            [
                html.Div(
                        
                        [
                            html.H5("Data By Day of Week"),
                            dbc.Row(
                                [
                                    dbc.Col(bar_data_scope_radio_items, class_name="col-md-2 text-left"),
                                    dbc.Col(bar_data_type_radio_items, class_name="col-md-2 text-left"),
                                    dbc.Col(bar_data_select_list, class_name="col-md-6 text-left")
                                ],
                                class_name="justify-content-start"
                            ),
                            dcc.Graph(
                                id="bar-graph", 
                                config = {
                                            "fillFrame": False,
                                            "showTips":True
                                            }
                                )
                        ],
                        className="shadow-sm offset-md-1 col-md-4 border bg-white mr-2"
                ),
                html.Div(
                        [
                            dbc.Row(html.H5("Data Over Time")),
                            dbc.Row([
                                dbc.Col(
                                    trend_checklist,
                                    class_name="col-md-3"
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                             id="trend-graph"
                                            #  style={'width': '100%', 'height': '100%'}
                                             )
                                )
                                ],
                                align="center"
                              )
                            ],
                            className="shadow-sm ml-md-auto pl-3 col-md-6 border bg-white ml-2"
                        ),
            ],
            class_name = "mt-3"
          ),
          dbc.Row(
              [
                  dbc.Col(
                      [
                      html.H6("Stats", style={"align":"center"}),
                        dash_table.DataTable(
                            id='stats-table'
                        )
                      ],
                      width = {"size":10, "offset":1}
                  )
              ],
              align="center",
              class_name = "mt-3"
          )
      ],
      fluid=True
)

app.layout = html.Div([
    navbar,
    upload_modal,
    body
])

# Utility functions
def determine_table_name(scope_choice):
    if scope_choice == "whole":
        return "Summary"
    else:
        return "ArticleSection"

def format_select_query(query_args):
    query = '''
            SELECT *
            FROM {0}
            WHERE Date >= '{1}' AND
                  Date <= '{2}' 
        '''
    return query.format(*query_args)

def format_agg_query(query_args):
      query = '''
            SELECT {0}, {1}({2}) As {2}
            FROM {3}
            WHERE Date >= '{4}' AND
                  Date <= '{5}'
            GROUP BY {0}
            '''
      return query.format(*query_args)

def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    Output('bar-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('bar-data-choice', 'value'),
    Input('bar-scope-choice', 'value'),
    Input('bar-type-choice', 'value')])
def update_bar_figure(start_date, end_date, bar_choice, bar_scope, bar_data_type):
    conn = sqlite3.connect(sqlite_path)

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_dict = {}
    for idx, weekday in enumerate(weekdays):
        weekday_dict[idx] = weekday

    if bar_data_type == "sum":
        query_agg_func = "SUM"
        y_axis_label_prefix = "Total"
    else:
        query_agg_func = "AVG"
        y_axis_label_prefix = "Average"

    layout = {
        "margin":{"t":20, "l":40, "b":40},
        "xaxis": {"title": "Weekday"}, 
        "yaxis": {"title": " ".join([y_axis_label_prefix, bar_choice])}
        #"title":{"text":bar_choice, "xanchor":"left"}
    }
    
    if " " in bar_choice:
        query_column = "`%s`" % bar_choice
    else:
        query_column = bar_choice

    if bar_scope == "whole":
        
        table_name = "Summary"
        group_column = "Weekday"
        query_args = [group_column, query_agg_func, query_column, table_name, start_date, end_date]
        query = format_agg_query(query_args)
        df_group_by_wd = pd.read_sql(query, conn)
        df_group_by_wd.Weekday = df_group_by_wd.Weekday.map(weekday_dict)
        fig = px.bar(df_group_by_wd, x="Weekday", y=bar_choice)

    else:

        group_column = "Weekday, ArticleNumber"
        table_name = "ArticleSection"
        query_args = [group_column, query_agg_func, query_column, table_name, start_date, end_date]
        query = format_agg_query(query_args)
        df_group_by_wd = pd.read_sql(query, conn)
        df_group_by_wd.Weekday = df_group_by_wd.Weekday.map(weekday_dict)
        section_names = ["Story 1", "Story 2", "Story 3", "Other Headlines", "MOTD"]
        section_dict = {}

        for idx, section_name in enumerate(section_names):
            section_dict[idx] = section_name

        df_group_by_wd.ArticleNumber = df_group_by_wd.ArticleNumber.map(section_dict)
        trace_data = list()
        for article_num in [0, 1, 2, 3, 4]:
            data = df_group_by_wd.query("ArticleNumber == '{0}'".format(section_dict[article_num]))
            trace_data.append(
                go.Bar(x = data["Weekday"], y=data[bar_choice], name=section_dict[article_num])
            )

        fig = go.Figure(data=trace_data, layout=layout)
    # fig.update_layout(legend=dict(
    #                     yanchor="top",
    #                     y=0.99,
    #                     xanchor="right",
    #                     x=0.99
    #                     )
    #                 )
    return fig

@app.callback(
    Output('trend-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('trend-data-choice', 'value')
    ])
def update_trend_figure(start_date, end_date, columns):
    conn = sqlite3.connect(sqlite_path)
    layout = {
            "margin":{"t":50, "r":10, "l":20, "b":20}
        }
    fig = go.Figure(layout=layout)
    table_name = "Summary"
    query_args = [table_name, start_date, end_date]
    query = format_select_query(query_args)
    df = pd.read_sql(query, conn, index_col="Date")

    for column in columns:
        fig.add_trace(
            go.Scatter(x = df.index, y = df[column], mode="markers", name=column)
        )
    fig.update_layout(legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                    )
                  )
    return fig

@app.callback(
    Output('stats-table', 'data'),
    Output('stats-table', 'columns')
    ,
    [Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date')
    ])
def update_stats_table(start_date, end_date):
    conn = sqlite3.connect(sqlite_path)
    table_name = "Summary"
    query_args = [table_name, start_date, end_date]
    query = format_select_query(query_args)
    df = pd.read_sql(query, conn, index_col="Date")
    min_to_max = df.describe().transpose()[["min","25%","50%","75%","max"]][0:8]
    min_to_max.reset_index(inplace=True)
    min_to_max.rename(columns={"index":"Measure"}, inplace=True)
    data = min_to_max.to_dict("records")
    columns = [{"name":column, "id":column} for column in min_to_max.columns]
    return [data, columns]

@app.callback(
    [Output('bar-data-choice', 'options'), Output('bar-data-choice', 'value')],
    Input('bar-scope-choice', 'value')
)
def update_bar_options(scope_choice):
    if scope_choice == "whole":
        return [{"label":col, "value":col} for col in numeric_columns_summary], numeric_columns_summary[0]
    else:
        return [{"label":col, "value":col} for col in numeric_columns_section], numeric_columns_section[0]

@app.callback(
    Output("file-list", "children"),
    [Input("file-upload", "filename")],
)
def list_uploaded_files(uploaded_filenames):
    
    if type(uploaded_filenames) == list:
        files = uploaded_filenames
        return [html.Li(filename) for filename in files]

@app.callback(
    Output("upload-success-label","children"),
    [Input("file-upload", "filename"), 
     Input("file-upload", "contents"),
     Input("upload-files-button", "n_clicks")],
)
def upload_files(uploaded_filenames, uploaded_contents, n_clicks):
    
    if type(uploaded_filenames) == list and n_clicks:
        try:
            for filename, filecontent in zip(uploaded_filenames, uploaded_contents):
                base64_content_str = filecontent.split('base64,')[1]
                decoded_bytes = base64.b64decode(base64_content_str)
                with open("data/raw/uploads/{0}".format(filename), "wb") as fb:
                    fb.write(decoded_bytes)
            return [dbc.Label("File upload was successful!")]
        except:
            return [dbc.Label("File upload was not successful...")]


app.callback(
    Output("upload-modal", "is_open"),
    [
        Input("upload-button", "n_clicks"),
        Input("close-modal", "n_clicks"),
    ],
    [State("upload-modal", "is_open")],
)(toggle_modal)

if __name__ == "__main__":
    app.run_server(debug=True)