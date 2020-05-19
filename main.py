import dash
import dash_core_components as dcc
import dash_html_components as html
import redis
import flask
import time
import os
import json


def db_connect():
    r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

    d = {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'}
    r.set('data', json.dumps(d))

    return json.loads(r.get('data'))


def init_flask():
    server = flask.Flask('app')
    server.secret_key = os.environ.get('secret_key', 'secret')
    return server


def init_dash(server, data):
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
            Dash: A web application framework for Python.
        '''),

        dcc.Graph(
            id='example-graph',
            figure={
                'data': [
                    data,
                ],
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }
        )
    ])
    app.run_server(debug=True)


if __name__ == '__main__':
    data = db_connect()
    server = init_flask()
    init_dash(server, data)
