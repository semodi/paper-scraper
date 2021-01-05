import pandas as pd
import pymysql
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import datetime
import requests
import json
import mysql_config
import warnings
import time
import pickle
import graph
# recommender_url = 'https://mf9ay4s4u2.execute-api.us-east-2.amazonaws.com/default/'
recommender_url = 'http://localhost:6545/api/'
# Test user
USERNAME = 'johndoe'
U_ID = 0
def connect():
    return pymysql.connect(host=mysql_config.host,
                       user=mysql_config.name,
                       passwd=mysql_config.password,
                       connect_timeout=5,
                       database='arxiv',
                       port=mysql_config.port)

# r = requests.post(recommender_url + 'index/')


def get_recommendations(no_papers=10, cutoff_days = 20, based_on = None, return_A = False):
    # Recommendations based on saved bookmarks
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    data = {'user_id': U_ID, 'no_papers':no_papers, 'cutoff_days': cutoff_days, 'based_on': based_on}
    data = json.dumps(data)
    try:
        r = requests.post(recommender_url + 'recommend', data=data, headers=headers)
        recommendations = json.loads(r.text)
        distances = recommendations['distances']
        query = recommendations['query']
        recommendations = recommendations['recommendations']
    except Exception as e:
        print(e)
        print('Recommendations could not be retrieved')
        recommendations = []
        query = []
        distances = [[0]]
    # recommendations = []
    # with open('recfile.pckl', 'rb') as file:
    #     recommendations = pickle.load(file)
    cond_rec = [{
                'if': {
                    'filter_query': '{{id}} = {}'.format(r['id']) # matching rows of a hidden column with the id, `id`
                },
                'color': 'tomato',
                'fontWeight': 'bold'
                } for r in recommendations]
    if return_A:
        return cond_rec, recommendations, query, distances
    else:
        return cond_rec, recommendations

cond_rec, recommendations, query, distances = get_recommendations(return_A=True)
display_columns = ['title', 'authors']
day = lambda i: '{:d} days ago'.format(abs(i)) if i != 0 else 'today'

network_fig, colors = graph.get_graph(query + recommendations, distances, n_query=len(query))
# =============== LAYOUT ===================

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'paper-scraper'
# app = dash.Dash(
#     __name__,
#     meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
# )
panel_color = '#161a28'
suffix_row = "_row"
suffix_button_id = "_button"
suffix_sparkline_graph = "_sparkline_graph"
suffix_count = "_count"
suffix_ooc_n = "_OOC_number"
suffix_ooc_g = "_OOC_graph"
suffix_indicator = "_indicator"
app.layout = html.Div(children=
    [

    html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("paper-scraper"),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    # html.Button(
                    #     id="learn-more-button", children="LEARN MORE", n_clicks=0
                    # ),
                    html.Div(className='five columns', children=[
                        html.P(),
                        html.P('created with')
                    ]),
                    html.Img(id="logo", src=app.get_asset_url("dash-logo-new.png")),
                ],
            ),
        ],
    ),
    html.Div(children=[
        dcc.Tabs(id='tabs',value='tab1', className='custom-tabs', children=[
            dcc.Tab(id='Recent-tab',label='Recent papers', value='tab1',
             className='custom-tab',selected_className='custom-tab--selected', children=[
            # html.Div(className='row', children=
            #     [
                html.Div([
                html.Div(className='row', children=
                    [
                    html.P(id='buffer2', style={'marginTop':'2 rem'}),
                    html.Label('Number of papers'),
                    dcc.Slider(
                        id='slider-no-papers',
                        min=5,
                        max=100,
                        step=1,
                        value=15,
                        marks={i:'{:d}'.format(i) for i in range(10,101,10)}
                    ),
                    ], style={'marginBottom': '2em','marginLeft': '8em','marginRight': '8em'}
                ),
                html.Div(
                    [
                    html.Label('Publication date'),
                    dcc.RangeSlider(
                        id='time-slider',
                        min=-30,
                        max=0,
                        step=1,
                        value=[-10,0],
                        marks={i:day(i) for i in range(-30,1,5)}
                    ),
                    ], style={'marginBottom': '3em','marginLeft': '8em','marginRight': '8em'}
                ),
                html.Div([
                dash_table.DataTable(
                    id='table-papers',
                    # style_cell={
                    #     'whiteSpace': 'normal',
                    #     'height': 'auto',
                    #     'width': '60%'
                    # },
                    style_header={"fontWeight": "bold", "color": "inherit"},
                    style_as_list_view=True,
                    fill_width=True,
                    style_cell={
                        "backgroundColor": "#1e2130",
                        "fontFamily": "Open Sans",
                        "padding": "0 2rem",
                        "color": "darkgray",
                        "border": "none",
                        "width" : '60%',
                        "height" : 'auto',
                        "whiteSpace" : 'normal'
                    },
                    css=[
                        {"selector": "tr:hover td", "rule": "color: #91dfd2 !important;"},
                        {"selector": "td", "rule": "border: none !important;"},
                        {
                            "selector": ".dash-cell.focused",
                            "rule": "background-color: #1e2130 !important;",
                        },
                        {"selector": "table", "rule": "--accent: #1e2130;"},
                        {"selector": "tr", "rule": "background-color: transparent"},
                    ],
                    style_data_conditional= cond_rec,
                    row_selectable="multi",
                    columns=[{"name": i, "id": i} for i in display_columns],
        #             data=df.to_dict('records'),
                    style_table={'width': '100%', 'height': 500,'overflowY':'scroll'})
                    ],className='eleven columns'),
                html.Button('Bookmark selected',
                            id ='bookmark-button'),
                html.P(id='updated-bookmarks',children=1,hidden=True),
                # ]),
                ],style={'backgroundColor':panel_color}),
            ],style = {'backgroundColor':panel_color}),
            dcc.Tab(id='Rec-tab',label='Recommended', value='tab2',
             className='custom-tab',selected_className='custom-tab--selected', children=[
            # html.Div(className='row', children=
            #     [
                html.Div([
                html.Div(className='row', children=
                    [
                    html.P(id='buffer1', style={'marginTop':'2 rem'}),
                    html.Label('Number of papers'),
                    dcc.Slider(
                        id='slider-no-papers-rec',
                        min=5,
                        max=100,
                        step=1,
                        value=15,
                        marks={i:'{:d}'.format(i) for i in range(10,101,10)}
                    ),
                    ], style={'marginBottom': '2em','marginLeft': '8em','marginRight': '8em'}
                ),
                html.Div(
                    [
                    html.Label('Publication date'),
                    dcc.Slider(
                        id='time-slider-rec',
                        min=0,
                        max=30,
                        step=1,
                        value=20,
                        marks={i:day(-i) for i in range(0,31,5)}
                    ),
                    ], style={'marginBottom': '3em','marginLeft': '8em','marginRight': '8em'}
                ),
                html.Div([
                dash_table.DataTable(
                    id='table-rec',
                    # style_cell={
                    #     'whiteSpace': 'normal',
                    #     'height': 'auto',
                    #     'width': '60%'
                    # },
                    style_header={"fontWeight": "bold", "color": "inherit"},
                    style_as_list_view=True,
                    fill_width=True,
                    style_cell={
                        "backgroundColor": "#1e2130",
                        "fontFamily": "Open Sans",
                        "padding": "0 2rem",
                        "color": "darkgray",
                        "border": "none",
                        "width" : '60%',
                        "height" : 'auto',
                        "whiteSpace" : 'normal'
                    },
                    css=[
                        {"selector": "tr:hover td", "rule": "color: #91dfd2 !important;"},
                        {"selector": "td", "rule": "border: none !important;"},
                        {
                            "selector": ".dash-cell.focused",
                            "rule": "background-color: #1e2130 !important;",
                        },
                        {"selector": "table", "rule": "--accent: #1e2130;"},
                        {"selector": "tr", "rule": "background-color: transparent"},
                    ],
                    row_selectable="multi",
                    columns=[{"name": i, "id": i} for i in display_columns],
        #             data=df.to_dict('records'),
                    style_table={'width': '100%', 'height': 500,'overflowY':'scroll'})
                    ],className='eleven columns'),
                html.Button('Bookmark selected',
                            id ='bookmark-button-rec'),
                html.P(id='updated-bookmarks-rec',children=1,hidden=True),
                # ]),
                ],style={'backgroundColor':panel_color}),
            ]),
        dcc.Tab(id='Exp-tab',label='Explore',value='tab3',
        selected_className='custom-tab--selected',
        className='custom-tab', children = [
            html.P(id='buffer3', style={'marginTop':'2 rem'}),
            dcc.Graph(id='network-graph', figure=network_fig, style={'width':'100%','height':500}),
            html.Button('Reset',id ='reset-button'),
            html.Button('Bookmark',id ='bookmark-button-explore'),
            html.Div(id='hidden-graphs', children=[
            dcc.Graph(id='network-graph-master', figure=network_fig),
            dcc.Graph(id='network-graph-1', figure=network_fig),
            dcc.Graph(id='network-graph-2', figure=network_fig),
            dcc.Graph(id='network-graph-3', figure=network_fig),
            dcc.Graph(id='network-graph-4', figure=network_fig),
            html.P(id='zoomed-in'),
            html.Div(id='hover-data'),
            ],style={'display':'none'})
        ])
    ])
    ], className='tabs six columns'),
#         ]),
    html.Div(
        [
        # html.H3('Info'),

        # dcc.Textarea(
        #     id='textarea-abstract',
        #     value='Textarea content initialized\nwith multiple lines of text',
        #     style={'width': '100%', 'height': 300}),
        # html.Br(),
        html.Div(className='twelve columns', children = [
        html.Div(className='section-banner',children='Info'),
        html.Div(className='eleven columns', children = [
        html.Br(),
        html.Center([
        dcc.Markdown(
            id='textarea-abstract',
            children='Click on entry to display information',
            style={'width': '99%', 'height': 337,'overflowY':'scroll','text-align':'left'}),
        ]),
        html.A(id='gotolink', children='Go to paper', href='http://www.google.com'),])
        ],style={'backgroundColor':panel_color, 'marginBottom':'1rem'}),
        html.Div(className='twelve columns', children = [
            html.Div(className='section-banner',children='Bookmarked'),
            # html.H3('Bookmarked'),
            html.Div(className='eleven columns', children = [
            dash_table.DataTable(
                id='table-bookmarks',
                style_header={"fontWeight": "bold", "color": "inherit"},
                style_as_list_view=True,
                fill_width=True,
                style_cell={
                    "backgroundColor": "#1e2130",
                    "fontFamily": "Open Sans",
                    "padding": "0 2rem",
                    "color": "darkgray",
                    "border": "none",
                    "width" : '60%',
                    "height" : 'auto',
                    "whiteSpace" : 'normal'
                },
                css=[
                    {"selector": "tr:hover td", "rule": "color: #91dfd2 !important;"},
                    {"selector": "td", "rule": "border: none !important;"},
                    {
                        "selector": ".dash-cell.focused",
                        "rule": "background-color: #1e2130 !important;",
                    },
                    {"selector": "table", "rule": "--accent: #1e2130;"},
                    {"selector": "tr", "rule": "background-color: transparent"},
                ],
                columns=[{"name": i, "id": i} for i in display_columns],
    #             data=df_bookmarks.to_dict('records'),
                style_table={'width': '99%', 'height': 308,'overflowY':'scroll'}),
                ]),
                html.P(id='selected-bookmarks'), # Hacky workaround bc. dash would mix up callbacks between tables
                html.P(id='selected-papers'),
                html.P(id='selected-rec'),
                html.P(id='loading-rec'),
                html.P(id='placeholder'),
        ],style={'backgroundColor':panel_color}),
        ], className='five columns'),
#          ]),

    ], className = 'row'
)

# ============= CALLBACKS =================

@app.callback(
      Output('updated-bookmarks','children'),
      [Input('bookmark-button', 'n_clicks'),
       Input('bookmark-button-rec', 'n_clicks'),
       Input('bookmark-button-explore','n_clicks')],
      [State('table-papers','selected_rows'),
       State('table-papers','data'),
       State('table-rec', 'selected_rows'),
       State('table-rec', 'data'),
       State('network-graph','hoverData')])
def bookmark_papers(_, __, ___, rows_pap, data_pap, rows_rec, data_rec,hover_data):

    ctx = dash.callback_context
    ctx = ctx.triggered[0]['prop_id']
    if ctx == 'bookmark-button.n_clicks':
        rows = rows_pap
        data = data_pap
    elif ctx == 'bookmark-button-rec.n_clicks':
        rows = rows_rec
        data = data_rec
    elif ctx == 'bookmark-button-explore.n_clicks':
        if hover_data is not None:
            rows = [0]
            data = [json.loads(hover_data['points'][0]['customdata'])]
        else:
            rows = []
    else:
        rows = []

    updated = False
    conn = connect()
    c = conn.cursor()
    # Load user's bookmarks into memory
    df = pd.read_sql(""" SELECT  * FROM bookmarks
                WHERE user_id = {:d} """.format(U_ID), conn)
    for row in rows:
        # Check if bookmark already exists
        if not data[row]['id'] in df['article_id'].values:
            updated  = True
            c.execute(''' INSERT INTO bookmarks
             values (NULL, %s, %s, %s)''',(data[row]['id'], U_ID, datetime.datetime.now()))
    conn.commit()
    conn.close()

    return int(updated)

@app.callback(
      Output('table-bookmarks','data'),
      Input('updated-bookmarks','children'),
      State('table-bookmarks','data'))
def update_bookmark_table(value, data):
    if value or data is None:

        conn = connect()
        df_bookmarks = pd.read_sql(""" SELECT
                                   articles.id as id,
                                   bookmarks.user_id as user_id,
                                   bookmarks.created,
                                   updated,
                                   authors,
                                   title,
                                   summary
                                   FROM articles
                                   INNER JOIN bookmarks
                                   ON articles.id = bookmarks.article_id
                                   WHERE bookmarks.user_id = {}
                                   ORDER BY bookmarks.created DESC""".format(U_ID), conn)
        conn.close()
        return df_bookmarks.to_dict('records')
    else:
        print('Nothing to update')
        return data


# @app.callback(
#         Output('network-graph', 'figure'),
#         Input('reset-button','n_clicks'),
#         State('network-graph-master', 'figure'))
# def reset_default(clicks, fig):
#     print(clicks)
#     print('default', fig is None)
#     if fig:
#         return fig
#



@app.callback(
    [Output('textarea-abstract','children'),
     Output('gotolink','children'),
     Output('gotolink','href'),
     Output('selected-bookmarks','value'),
     Output('selected-papers','value'),
     Output('selected-rec', 'value')],
    [Input('table-bookmarks','active_cell'),
     Input('table-papers','active_cell'),
     Input('table-rec','active_cell'),
     Input('network-graph', 'hoverData')],
    [State('table-bookmarks','data'),
     State('table-papers','data'),
     State('table-rec','data'),
     State('selected-bookmarks','value'),
     State('selected-papers','value'),
     State('selected-rec', 'value')])
def get_active(active_cell_bm, active_cell_p, active_cell_rec, hoverData, data_bm, data_p, data_rec, sbm, sp, srec):
    """ Check which paper selected and display its summary"""

    def get_summary(row):
        return '**' + row['title'] + '** \n\n *' + row['authors'] + '*\n\n' + \
        'Updated: ' + row['updated'].split('T')[0] + '\n\n' + \
        row['summary'].replace('\n',' ')

    if hoverData:
        based_on = json.loads(hoverData['points'][0]['customdata'])
        summary = get_summary(based_on)

        return summary,'Go to paper', based_on['id'], sbm, sp, srec

    else:
        if active_cell_bm and active_cell_bm != sbm:
            row = active_cell_bm['row']
            summary = get_summary(data_bm[row])
            sbm = active_cell_bm
            return summary,'Go to paper',data_bm[row]['id'], sbm, sp, srec
        elif active_cell_p and active_cell_p != sp:
            row = active_cell_p['row']
            summary = get_summary(data_p[row])
            sp = active_cell_p
            return summary,'Go to paper',data_p[row]['id'], sbm, sp, srec
        elif active_cell_rec :
            row = active_cell_rec['row']
            summary = get_summary(data_rec[row])
            sp = active_cell_rec
            return summary,'Go to paper',data_rec[row]['id'], sbm, sp, srec
        else:
            return 'Click on entry to display information','Go to paper','', sbm, sp, srec



@app.callback(
        [Output('table-papers','style_data_conditional'),
        Output('table-rec', 'data'),
        Output('network-graph-master', 'figure'),
        Output('table-bookmarks','style_data_conditional')],
        [Input('time-slider-rec', 'value'),
         Input('slider-no-papers-rec', 'value')])
def update_recommendations(time_lim, no_papers):
    cond_rec, recommendations, query, distances = get_recommendations(no_papers, time_lim, return_A=True)

    total = query + recommendations
    network_fig_, colors = graph.get_graph(total, distances, n_query=len(query))
    cond_rec_bm = [{
            'if': {
                'filter_query': '{{id}} = {}'.format(r['id']) # matching rows of a hidden column with the id, `id`
            },
            'color': c,
            } for r, c in zip(total,colors)]

    return cond_rec, recommendations, network_fig_, cond_rec_bm

@app.callback(
        Output('table-papers', 'data'),
        [Input('time-slider', 'value'),
         Input('slider-no-papers', 'value')])
def filter_papers(time_lim, no_papers):
    """ Apply number and date filter to displayed papers"""
    conn = connect()
    query = """ SELECT
                    *
                    FROM articles
                    WHERE DATE(updated) > DATE_ADD(DATE(NOW()),INTERVAL {:d} day)
                    AND  DATE(updated) < DATE_ADD(DATE(NOW()), INTERVAL {:d} day) LIMIT {:d} """.format(time_lim[0],
                                                                                                          time_lim[1],
                                                                                                          no_papers)
    df = pd.read_sql(query, conn)
    conn.close()

    return df.to_dict('records')

@app.callback(
    [Output('network-graph', 'figure'),
     Output('network-graph-1', 'figure'),
     Output('zoomed-in', 'value')],
    [Input('network-graph', 'clickData'),
    Input('network-graph-master', 'figure'),
    Input('reset-button','n_clicks')],
    [State('network-graph', 'figure'),
    State('network-graph-1', 'figure'),
    State('zoomed-in','value')], prevent_initial_call=True)
def display_click_data(clickData,fig_master,n_clicks, fig, fig_1,zoomed):
    ctx = dash.callback_context
    ctx = ctx.triggered[0]['prop_id']
    if ctx == 'network-graph.clickData' and clickData:
        based_on = [json.loads(clickData['points'][0]['customdata'])]
        curve_no = clickData['points'][0]['pointNumber']
        if zoomed and curve_no == 0:
            return fig_1, fig_master, 0
        cond_rec, recommendations, query, distances = get_recommendations(10, 10000,
        based_on = based_on, return_A=True)

        total = query + recommendations
        network_fig, colors = graph.get_graph(total, distances, n_query=1)
        return network_fig, fig, 1
    elif ctx in ['network-graph-master.figure','reset-button.n_clicks']:
        return fig_master, fig_master, 0
    else:
        return fig, fig_1, 0

@app.callback(
    Output('network-graph','hoverData'),
    Input('tabs','value')
)
def reset_hover_data(inp):
    return None

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
