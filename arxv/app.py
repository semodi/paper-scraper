import arxiv
from flask import Flask, request, redirect, url_for, flash, jsonify
import pymysql
import pandas as pd
import datetime
import time
import mysql_config
import sys
import logging
MAX_ARTICLES = 10000

def make_entry(d):
    """ Create database entry from query result"""
    id_ = d['id']
    updated = datetime.datetime.strptime(d['updated'], '%Y-%m-%dT%H:%M:%SZ')
    title = d['title']
    summary = d.get('summary','')
    tags = ', '.join([v['term'] for v in d['tags']])
    authors = ', '.join(d['authors'])
    return id_, updated, title, summary, tags, authors

def pull_data():
    conn = pymysql.connect(mysql_config.host,
                           user=mysql_config.name,
                           passwd=mysql_config.password,
                           connect_timeout=5,
                           port=mysql_config.port)
    c = conn.cursor()
    c.execute(''' create database if not exists arxiv''')
    conn.commit()
    conn.close()

    conn = pymysql.connect(mysql_config.host,
                           user=mysql_config.name,
                           passwd=mysql_config.password,
                           db = 'arxiv',
                           connect_timeout=5,
                           port=mysql_config.port)
    c = conn.cursor()

    c.execute('''create table if not exists articles
                (id VARCHAR(100) unique, updated DATETIME, title TINYTEXT, summary TEXT, tags TINYTEXT, authors MEDIUMTEXT)''')

    c.execute('''create table if not exists users
                (id INTEGER NOT NULL AUTO_INCREMENT,
                created DATETIME,
                name VARCHAR(100),
                PRIMARY KEY (id))''')

    if not len(pd.read_sql(''' SELECT * FROM users''', conn)): #Add test user if table empty
        c.execute('''insert into users (id, created, name)
                      values (NULL, %s, %s)''',
                      (datetime.datetime.now(),'johndoe'))

    c.execute('''create table if not exists bookmarks
                (id INTEGER NOT NULL AUTO_INCREMENT,
                 article_id VARCHAR(100),
                 user_id INTEGER,
                 created DATETIME,
                 PRIMARY KEY(id))''')


    latest = pd.read_sql('''SELECT
                Max(updated) as dt
                FROM articles''', conn)['dt'][0]

    starting_over = False
    if not latest:
        logging.warning('No articles contained in table. Starting over...')
        latest = datetime.datetime(1900, 1, 1,1,1,1)
        starting_over = True

    cnt = 0
    for start in range(0, MAX_ARTICLES, 1000):
        if starting_over: logging.warning('{:d}/{:d} articles added'.format(start, MAX_ARTICLES))
        for q in arxiv.query('cat:cs.LG',max_results=1000, start=start, sort_by='submittedDate'):
            entry = make_entry(q)
            this_time = entry[1]
            if this_time <= latest:
                break
            else:
                c.execute('''insert into articles
                             values (%s, %s, %s, %s, %s, %s)''',entry)
                cnt += 1
        else:
            continue
        break
    logging.warning('Total number of articles added: {:d}'.format(cnt))
    conn.commit()
    conn.close()

    return 'Total number of articles added: {:d}'.format(cnt)


app = Flask(__name__)


@app.route('/api/update', methods=['POST'])
def get_recommendation():
    try:
        pull_data()
        return "{ Success }"
    except:
        return "{An error occured while trying to update the database}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0',port='6540')
