import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import flask
import os
import json
import pandas as pd
import yaml
from lib import sems_utils as util


def create_df(data, match, vertices, common):
    end_time = pd.to_datetime(common.start_time) + (pd.to_timedelta(common.intervals) * (common.timesteps - 1))
    df_list = {}

    for vertex in vertices:
        if vertex in data.keys():
            data[vertex] = json.loads(data[vertex])
            data_list = data[vertex][match + vertex][:common.timesteps]

            if len(data_list) is not common.timesteps:
                for x in range(len(data_list), common.timesteps):
                    data_list.append('')

            df = pd.DataFrame(data_list, columns=['Reading'])
            df['Date'] = pd.date_range(common.start_time, end_time, freq=common.intervals).strftime('%H:%M:%S')
            df_list[vertex] = df

        else:
            df_list[vertex] = 'No data for {}'.format(vertex)

    return df_list


def multi_bar_graph(graph_name, id, params, graphs, common):
    #TODO: Group bar charts
    match = common.name + ":DATA:" + id + ":"
    data = util.get_data(match=match, vertex_list=params)
    df_list = create_df(dict(data), match, params, common)

    graph_data = []
    vertex = params[0]
    df = df_list[vertex]

    if type(df) is not str:
        graph_data.append(go.Bar(
            x=df.Date,
            y=df.Reading,
            name=vertex)
        )
    else:
        return html.Div([html.H3(children=df)], className="four columns")

    return html.Div(dcc.Graph(
        figure=go.Figure(data=graph_data,
                         layout=dict(
                             title_text=graphs[graph_name]['title']
                         )
                         )
    ))


def single_bar_graph(graph_name, id, params, graphs, common):
    match = common.name + ":DATA:" + id + ":"
    data = util.get_data(match=match, vertex_list=params)
    df_list = create_df(dict(data), match, params, common)

    graph_data = []
    vertex = params[0]
    df = df_list[vertex]

    if type(df) is not str:
        graph_data.append(go.Bar(
            x=df.Date,
            y=df.Reading,
            name=vertex)
        )
    else:
        return html.Div([html.H3(children=df)], className="four columns")

    return html.Div(dcc.Graph(
        figure=go.Figure(data=graph_data,
                         layout=dict(
                             title_text=graphs[graph_name]['title']
                         )
                         )
    ))


def multi_value_graph(graph_name, id, params, graphs, common):
    match = common.name + ":DATA:" + id + ":"
    data = util.get_data(match=match, vertex_list=params)
    df_list = create_df(dict(data), match, params, common)
    div_list = []
    graph_data = []

    for vertex in params:
        df = df_list[vertex]
        if type(df) is not str:
            graph_data.append(go.Scatter(
                x=df.Date,
                y=df.Reading,
                mode='lines',
                name=vertex)
            )
        else:
            div_list.append(html.Div([html.H3(children=df)]))
    div_list.append(html.Div(dcc.Graph(
        id='graph-{}'.format(graph_name),
        figure=go.Figure(data=graph_data,
                         layout=dict(
                             title_text=graphs[graph_name]['title']
                         )
                         )
    )))

    return div_list


def single_value_graph(graph_name, id, params, graphs, common):
    match = common.name + ":DATA:" + id + ":"
    data = util.get_data(match=match, vertex_list=params)
    df_list = create_df(dict(data), match, params, common)

    graph_data = []
    vertex = params[0]
    df = df_list[vertex]

    if type(df) is not str:
        graph_data.append(go.Scatter(
            x=df.Date,
            y=df.Reading,
            mode='lines',
            name=vertex)
        )
    else:
        return html.Div([html.H3(children=df)], className="four columns")

    return html.Div(dcc.Graph(
        figure=go.Figure(data=graph_data,
                         layout=dict(
                             title_text=graphs[graph_name]['title']
                         )
                         )
    ))


def create_graphs(id, graphs, common):
    div_list = []
    for graph in graphs:
        params = graphs[graph]['params']
        func = graphs[graph]['graph-function']

        result = globals()[func](graph, id, params, graphs, common)
        if type(result) is list:
            for div in result:
                div_list.append(div)
        else:
            div_list.append(result)
    return div_list


def init_flask():
    server = flask.Flask('SEMS-UI')
    server.secret_key = os.environ.get('secret_key', 'secret')
    return server


def init_dash(ids, common, graphs):
    server = init_flask()
    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

    app.layout = html.Div(children=[
        html.H1(children='Sustainability Energy Management System'),
        html.Div([
            dcc.Dropdown(
                id='results-dropdown',
                options=[{'label': _id, 'value': _id} for _id in ids],
                value=ids[0],
            ),

            html.Div(id='graphs')
        ]),
    ], className="row")

    @app.callback(Output(component_id='graphs', component_property='children'),
                  [Input(component_id='results-dropdown', component_property='value')]
                  )
    def display_graph(results_dropdown):
        return create_graphs(results_dropdown, graphs, common)

    app.run_server(debug=True)


class Common:
    pass


if __name__ == '__main__':
    config_file = open("sems-frontend.yaml")
    config = yaml.load(config_file, Loader=yaml.FullLoader)

    common = Common()
    common.name = "GREENWICH"
    common.start_time = "00:00:00"
    common.intervals = "15min"
    common.timesteps = 96

    ids = util.get_ids(match=common.name + ":DATA")
    init_dash(ids, common, config[common.name])
