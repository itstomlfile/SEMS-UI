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

df_list = dict()


def get_data(name):
    redis_conn = redis.Redis(host=HOST_NAME, port=PORT, db=DB, decode_responses=True)
    key_list = []
    for key in redis_conn.keys():
        if name in key:
            data = json.loads(redis_conn.get(key))
            key_list.append(key)
            df = pd.DataFrame(data[key], columns=['Reading'])
            df_list[key] = df

    return key_list


def create_graphs(key):
    df = pd.DataFrame(df_list[key], columns=['Reading'])
    df['Date'] = pd.date_range(START_TIME, END_TIME, freq=INTERVALS).strftime('%H:%M:%S')
    dummy_plot = go.Scatter(
        x=df.Date,
        y=df['Reading'],
        name="Dummy",
        line=dict(color='#17BECF'),
        opacity=0.8)

    layout = dict(
        title='Dummy Data',
        type='date'
    )

    data = [dummy_plot]
    fig = dict(data=data, layout=layout)

    return fig


def init_flask():
    server = flask.Flask('app')
    server.secret_key = os.environ.get('secret_key', 'secret')
    return server


def init_dash(keys):
    server = init_flask()
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[
        html.H1(children='SEMS'),

        html.Div(children='''
            SEMS UI
        '''),
        dcc.Dropdown(
            id='results-dropdown',
            options=[{'label': key, 'value': key} for key in keys],
            value=keys[0],
        ),
        html.Div([dcc.Graph(id="graph")])
    ])

    @app.callback(Output(component_id='graph', component_property='figure'),
                  [Input(component_id='results-dropdown', component_property='value')]
                  )
    def display_graphs(results_dropdown):
        fig = create_graphs(results_dropdown)
        return fig

    app.run_server(debug=True)


if __name__ == '__main__':
    keys = get_data(name=NAME)
    init_dash(keys)
