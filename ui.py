
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import pyarrow as pa
import redis
from datetime import datetime


red = redis.Redis(host='localhost', port=6379, db=0)
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colours = {
    'background': '#111111',
    'text': '#7FDBFF'
}

project_name = "GREENWICH"


def get_data(match, simplex):
    keys = []
    vertices = []

    for vertex in simplex:
        key = match + vertex
        if red.exists(key):
            keys.append(key)
            vertices.append(vertex)

    data = red.mget(keys)

    return dict(zip(vertices, data))


def gen_graph_child(ID, vertex, column):
    simplex = [vertex]
    # Get DATA
    title = project_name + " DATA: " + ID[0:4] + "-" + ID[4:6] + "-" + ID[6:8] \
                         + " " + ID[8:10] + ":" + ID[10:12] + ":" + ID[12:14] + " " + vertex
    data = get_data(project_name + ":DATA:" + ID + ":", simplex)
    # Get STATE
    # state_data = get_data(project_name + ":STATE:", simplex)

    context = pa.default_serialization_context()
    df = context.deserialize(data[vertex])
    df = df[column]
    #print("COLUMNS: ", df.columns)
    df.index = pd.to_datetime(df.index)

    return html.Div([
        html.Div([
            dcc.Graph(
                id=vertex + '-example-graph',
                figure={
                    'data': [
                        {'x': pd.to_datetime(df.index, infer_datetime_format=True),
                            'y': df,
                            'type': 'line', 'name': 'SF'}
                    ],
                    'layout': {
                        'plot_bgcolor': colours['background'],
                        'paper_bgcolor': colours['background'],
                        'font': {
                            'color': colours['text']
                        },
                        'title': title
                    }
                }
            )
        ],
        style={'width': '49%', 'display': 'inline-block'})
    ])


"""
@app.callback(
    Output('V-FCAST1-example-graph', 'figure'),
    [Input('id-selector', 'value')])
def update_figure(selected_id):
   """


if __name__ == '__main__':
    data_list = list(set([str(item).split(":")[2] for item in red.keys(project_name + ':DATA:*')]))
    top_level_namespaces = [{'label':str(item), 'value':item} for item in data_list]

    children = [
        html.Div([
            html.Label('Dropdown'),
            dcc.Dropdown(
                id="id-selector",
                options=top_level_namespaces,
                value=top_level_namespaces[0]['value']
            )
        ],
        style={'width': '49%', 'display': 'inline-block', 'font': {'color': colours['text']}}
        )
    ]

    ID = "20200420140133"

    children.append(gen_graph_child(
        ID=ID, vertex="EV-FCAST1", column="lamweek"))
    children.append(gen_graph_child(
        ID=ID, vertex="EV-FCAST2", column="lamweek"))
    children.append(gen_graph_child(
        ID=ID, vertex="EV-FCAST3", column="lamweek"))
    children.append(gen_graph_child(
        ID=ID, vertex="EV-FCAST4", column="lamweek"))
    children.append(gen_graph_child(
        ID=ID, vertex="EV-AGG", column="EVLoadWk"))

    app.layout = html.Div(
        style={'backgroundColor': colours['background'],
        'borderBottom': 'thin lightgrey solid',
        'padding': '10px 5px'},
        children=children)

    app.run_server(dev_tools_hot_reload=False, debug=True)