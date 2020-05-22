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


def get_data(key, redis_conn):
    if redis_conn.exists(key):
        data = json.loads(r.get(key))
        return data
    else:
        return


def create_graphs(data, key):
    # Testing with dummy data
    df = pd.DataFrame(list(data[key]), columns=['Reading'])
    df['Date'] = pd.date_range("00:00", "23:45", freq="15min")

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

    return dummy_plot, fig


def init_flask():
    server = flask.Flask('app')
    server.secret_key = os.environ.get('secret_key', 'secret')
    return server


def init_dash(server, data, fig):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        '''),
        dcc.Graph(id='my-graph', figure=fig)
    ])

    app.run_server(debug=True)


if __name__ == '__main__':
    project_name = "GREENWICH"
    ID = "20200420140133"
    name = "dummy"
    key = project_name + ":DATA:" + ID + ":" + name
    r = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)
    data = get_data(key=key, redis_conn=r)

    server = init_flask()
    graph, fig = create_graphs(data, key)
    init_dash(server, data, fig)
