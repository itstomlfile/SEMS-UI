import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import redis
import flask
import os
import json
import pandas as pd
import yaml
from lib import sems_utils as util

config_file = open("config.yaml")
config = yaml.load(config_file, Loader=yaml.FullLoader)

# YAML CONFIG VARIABLES
NAME = config['Data']['name']
HOST_NAME = config['Redis']['hostname']
PORT = config['Redis']['port']
DB = config['Redis']['db']
START_TIME = config['Data']['start_time']
END_TIME = config['Data']['end_time']
INTERVALS = config['Data']['intervals']
MATCH = NAME + ":DATA"
VERTICES = ["x", "y", "z"]

df_list = dict()


def create_df(data, match):
    for vertex in VERTICES:
        data[vertex] = json.loads(data[vertex])

        df = pd.DataFrame(list(data[vertex][match + vertex]), columns=['Reading'])
        df['Date'] = pd.date_range(START_TIME, END_TIME, freq=INTERVALS).strftime('%H:%M:%S')

        df_list[vertex] = df
    return df_list


def create_graphs(df_list):
    graph_list = []
    for vertex in df_list:
        df = df_list[vertex]
        graph_list.append(html.Div(dcc.Graph(
            id='graph-{}'.format(vertex),
            figure=dict(
                data=[dict(
                    x=df.Date,
                    y=df.Reading,
                )],
                layout=dict(
                    title=vertex,
                    type='date',
                )),
        ), className="four columns"))
    return graph_list


def init_flask():
    server = flask.Flask('SEMS-UI')
    server.secret_key = os.environ.get('secret_key', 'secret')
    return server


def init_dash(ids):
    server = init_flask()
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[

        html.H1(children='Sustainability Energy Management System'),

        # Col 1
        html.Div([
            dcc.Dropdown(
                id='results-dropdown',
                options=[{'label': id, 'value': id} for id in ids],
                value=ids[0],
            ),

            html.Div(id='graphs')

        ]),
    ], className="row")

    @app.callback(Output(component_id='graphs', component_property='children'),
                  [Input(component_id='results-dropdown', component_property='value')]
                  )
    def display_graph_1(results_dropdown):
        match = NAME + ":DATA:" + results_dropdown + ":"
        data = util.get_data(match=match, vertex_list=VERTICES)
        df_list = create_df(dict(data), match)
        fig = create_graphs(df_list)
        return fig

    app.run_server(debug=True)


if __name__ == '__main__':

    ids = util.get_ids(match=MATCH)

    init_dash(ids)
