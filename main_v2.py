import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import redis
import flask
import time
import os
import json
import dummy_data
import pandas as pd
import datetime as dt
from dash.dependencies import Input, Output

df_list = dict()


def get_data(name, redis_conn):
    keys = []
    for key in redis_conn.keys():
        if name in key:
            data = json.loads(r.get(key))
            keys.append(key)
            df = pd.DataFrame(data[key], columns=['Reading'])
            df['Date'] = pd.date_range("00:00:00", "23:59:00", freq="15min").strftime('%H:%M:%S')
            df_list[key] = df

    return keys


def create_graphs(key):
    # Testing with dummy data
    df = pd.DataFrame(df_list[key][1]), columns=['Reading'])
    print(df_list[key])
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


def init_dash(server, keys):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    dropdown_options = dict()
    ind = 0
    for key in keys:
        dropdown_options['result ' + str(ind)] = {'label': key, 'value': ind}
        ind = ind + 1

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[
        html.H1(children='SEMS'),

        html.Div(children='''
            SEMS UI
        '''),
        dcc.Dropdown(
            id='results-dropdown',
            options=[{'label': key, 'value': key} for key in keys],
            placeholder="Select a result",
        ),
        html.Div([dcc.Graph(id="graph")])
    ])

    @app.callback(Output(component_id='graph', component_property='figure'),
                  [Input(component_id='results-dropdown', component_property='value')]
                  )
    def display_graphs(results_dropdown):
        fig = create_graphs(key)
        return fig

    app.run_server(debug=True)


if __name__ == '__main__':
    project_name = "GREENWICH"
    r = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    keys = get_data(name=project_name, redis_conn=r)

    server = init_flask()
    init_dash(server, keys)
