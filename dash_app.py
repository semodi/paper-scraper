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
recommender_url = 'https://mf9ay4s4u2.execute-api.us-east-2.amazonaws.com/default/'

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


def get_recommendations():
    # Recommendations based on saved bookmarks
    data = {'user_id': U_ID, 'no_papers':1000}
    data = json.dumps(data)
    try:
        r = requests.post(recommender_url + 'recommend', data=data)
        recommendations = json.loads(r.text)
    except Exception as e:
        print(e)
        print('Recommendations could not be retrieved')
        recommendations = []
    # recommendations = []
    cond_rec = [{
                'if': {
                    'filter_query': '{{id}} = {}'.format(r['id']) # matching rows of a hidden column with the id, `id`
                },
                'color': 'tomato',
                'fontWeight': 'bold'
                } for r in recommendations]
    return cond_rec

cond_rec = get_recommendations()
display_columns = ['title', 'authors']
day = lambda i: '{:d} days ago'.format(-i) if i < 0 else 'today'

# =============== LAYOUT ===================

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    [
    html.Div(
        [
        html.H3('Recent Papers'),
        html.Div(
            [
            html.Label('Number of papers'),
            dcc.Slider(
                id='slider-no-papers',
                min=1,
                max=100,
                step=1,
                value=15,
                marks={i:'{:d}'.format(i) for i in range(10,101,10)}
            ),
            ], style={'marginBottom': '2em','marginLeft': '8em','marginRight': '8em'}
        ),
        html.Div(
            [
            html.Label('Time frame'),
            dcc.RangeSlider(
                id='time-slider',
                min=-30,
                max=0,
                step=1,
                value=[-5,0],
                marks={i:day(i) for i in range(-30,1,5)}
            ),
            ], style={'marginBottom': '3em','marginLeft': '8em','marginRight': '8em'}
        ),
        dash_table.DataTable(
            id='table-papers',
            style_cell={
                'whiteSpace': 'normal',
                'height': 'auto',
                'width': '60%'
            },
            style_data_conditional= cond_rec,
            row_selectable="multi",
            columns=[{"name": i, "id": i} for i in display_columns],
#             data=df.to_dict('records'),
            style_table={'width': '100%', 'height': 500,'overflowY':'scroll'}),
        html.Button('Bookmark selected',
                    id ='bookmark-button'),
        html.P(id='updated-bookmarks',children=1,hidden=True),
        ], className='six columns'),
#         ]),
    html.Div(
        [
        html.H3('Abstract'),
        dcc.Textarea(
            id='textarea-abstract',
            value='Textarea content initialized\nwith multiple lines of text',
            style={'width': '100%', 'height': 300}),
        html.A(id='gotolink', children='Go to paper', href='http://www.google.com'),
        html.H3('Bookmarked'),
        dash_table.DataTable(
            id='table-bookmarks',
            style_cell={
                'whiteSpace': 'normal',
                'height': 'auto',
                'width': '60%'
            },
            columns=[{"name": i, "id": i} for i in display_columns],
#             data=df_bookmarks.to_dict('records'),
            style_table={'width': '100%', 'height': 300,'overflowY':'scroll'}),
            html.P(id='selected-bookmarks'), # Hacky workaround bc. dash would mix up callbacks between tables
            html.P(id='selected-papers')
        ], className='six columns'),
#          ]),

    ], className = 'row'
)

# ============= CALLBACKS =================

@app.callback(
      Output('updated-bookmarks','children'),
      Input('bookmark-button', 'n_clicks'),
      [State('table-papers','selected_rows'),
       State('table-papers','data')])
def bookmark_papers(n_clicks, rows, data):
    updated = False
    if rows is not None:
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
                                   authors,
                                   title,
                                   summary
                                   FROM articles
                                   INNER JOIN bookmarks
                                   ON articles.id = bookmarks.article_id
                                   WHERE bookmarks.user_id = {}""".format(U_ID), conn)
        conn.close()
        return df_bookmarks.to_dict('records')
    else:
        print('Nothing to update')
        return data


@app.callback(
    [Output('textarea-abstract','value'),
     Output('gotolink','children'),
     Output('gotolink','href'),
     Output('selected-bookmarks','value'),
     Output('selected-papers','value')],
    [Input('table-bookmarks','active_cell'),
      Input('table-papers','active_cell')],
    [State('table-bookmarks','data'),
     State('table-papers','data'),
     State('selected-bookmarks','value'),
     State('selected-papers','value')])
def get_active(active_cell_bm, active_cell_p, data_bm, data_p, sbm, sp):
    """ Check which paper selected and display its summary"""
    if active_cell_bm and active_cell_bm != sbm:
        row = active_cell_bm['row']
        summary = data_bm[row]['summary'].replace('\n',' ')
        sbm = active_cell_bm
        return summary,'Go to paper',data_bm[row]['id'], sbm, sp
    elif active_cell_p and active_cell_p != sp:
        row = active_cell_p['row']
        summary = data_p[row]['summary'].replace('\n',' ')
        sp = active_cell_p
        return summary,'Go to paper',data_p[row]['id'], sbm, sp
    else:
        return '','','', sbm, sp

@app.callback(
        [Output('table-papers', 'data'),
        Output('table-papers', 'style_data_conditional')],
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

    cond_rec = get_recommendations()
    return df.to_dict('records'), cond_rec




if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')
