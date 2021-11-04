from datetime import datetime
import os
from dash import Dash
import dash_table
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from src import load_data

section_data_path = "data/processed/Article Section Data.csv"
summary_data_path = "data/raw/summary.xlsx"
article_html_folder_path = "data/raw/articles"

article_section_data = pd.read_csv(section_data_path, parse_dates=True, index_col="Date")
article_section_data.drop(labels="Unnamed: 0", axis=1, inplace=True)
summary_data = load_data.get_summary_data(summary_data_path)
data_start_date = summary_data.index[0].date()
article_list = [html_file.replace(".html", "") for html_file in os.listdir(article_html_folder_path)]
article_list_formatted = [{"label":article, "value":article} for article in article_list]

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
server = app.server

numeric_columns_summary = [
                            "Clicks", 
                            "Sends", 
                            "Opens",
                            "Open Rate",
                            "Send Rate",
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

bar_data_scope_radio_items = dcc.RadioItems(
                                id="bar-scope-choice",
                                options = [ 
                                    {"label":"Whole Article", "value":"whole"},
                                    {"label":"Whole Section", "value":"section"}
                                ],
                                value = "Whole Article"
                            )

bar_data_type_radio_items = dcc.RadioItems(
                                id="bar-type-choice",
                                options = [ 
                                    {"label":"Sum", "value":"sum"},
                                    {"label":"Average", "value":"avg"}
                                ],
                                value = "Whole Article"
                            )

bar_data_radio_items = dcc.RadioItems(
                        id="bar-data-choice",
                        labelStyle={'display': 'inline-block', "padding":"0.1em"}
                       )

trend_checklist = dcc.Checklist(
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
                            labelStyle={'display': 'inline-block', "padding":"0.1em"}
                       )

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("The Column Data Hub"),
            dbc.Row(
                [
                    dcc.DatePickerRange(
                                id='date-picker-range',
                                min_date_allowed = data_start_date,
                                max_date_allowed = datetime.now(),
                                start_date = data_start_date,
                                end_date = datetime.now()
                        )
                    ]
                ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True
)

#content = d

body = dbc.Container(
      [ 
          dbc.Row(
            [
              dbc.Col(
                  dbc.Card([
                        dbc.CardBody(
                            [
                                html.H6("Data By Day of Week"),
                                dbc.Row(
                                    bar_data_scope_radio_items
                                ),
                                dbc.Row(
                                    bar_data_type_radio_items
                                ),
                                dbc.Row(
                                    bar_data_radio_items
                                ),
                                dcc.Graph(id="bar-graph")
                            ]
                        )
                  ]
                )
              ),
            dbc.Col(
                   dbc.Card(
                    [
                        dbc.CardBody(
                            [
                            html.H6("Data By Over Time"),
                            dbc.Row(
                                trend_checklist
                            ),
                            dcc.Graph(id="trend-graph")
                            ]
                        )
                    ]
                )
              )
            ]
          ),
          dbc.Row(
              [
                  dbc.Col(
                      [
                      html.H6("Stats", style={"align":"center"}),
                        dash_table.DataTable(
                            id='stats-table'
                        )
                      ]
                  )
              ],
              align="center"
          )
      ]
)

app.layout = html.Div([
    navbar,
    body
])

# app.layout = dbc.Alert(
#     "Hello, Bootstrap!", className="m-5"
# )
def determine_data_source(scope):
    if scope == "whole":
        return summary_data
    else:
        return article_section_data


@app.callback(
    Output('bar-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('bar-data-choice', 'value'),
    Input('bar-scope-choice', 'value'),
    Input('bar-type-choice', 'value')])
def update_bar_figure(start_date, end_date, bar_choice, bar_scope, bar_data_type):
    df = determine_data_source(bar_scope).loc[start_date:end_date].copy()

    if bar_scope == "whole":
        if bar_data_type == "sum":
            df_group_by_wd = df.groupby("Weekday").sum()
            

        else:
            df_group_by_wd = df.groupby("Weekday").mean()

        fig = px.bar(df_group_by_wd, y=bar_choice)

    else:
        fig = go.Figure()

        if bar_data_type == "sum":
            df_group_by_wd_num = df.groupby(["Weekday", "ArticleNumber"]).sum().reset_index()
        else:
             df_group_by_wd_num = df.groupby(["Weekday", "ArticleNumber"]).mean().reset_index()
        
        for article_num in [0, 1, 2, 3, 4]:
            data = df_group_by_wd_num.query("ArticleNumber == {0}".format(article_num))
            fig.add_trace(
                go.Bar(x = data["Weekday"], y=data[bar_choice], name=str(article_num))
            )

    return fig

@app.callback(
    Output('trend-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('trend-data-choice', 'value')
    ])
def update_trend_figure(start_date, end_date, columns):
    fig = go.Figure()
    df = summary_data.loc[start_date:end_date]

    for column in columns:
        fig.add_trace(
            go.Scatter(x = df.index, y = df[column], mode="markers", name=column)
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
    df = summary_data.loc[start_date:end_date]
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

if __name__ == "__main__":
    app.run_server(debug=True)