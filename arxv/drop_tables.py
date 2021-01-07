import arxiv
import pymysql
import pandas as pd
import datetime
import time
import sys
import mysql_config

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == '-y':
        confirm = 'y'
    else:
        confirm = input('Sure? (y/N) ')

    if confirm.lower() == 'y':
        print('Dropping tables...')
        conn = pymysql.connect(mysql_config.host,
                           user=mysql_config.name,
                           passwd=mysql_config.password,
                           db = 'arxiv',
                           connect_timeout=5,
                           port=mysql_config.port)
        c = conn.cursor()
        c.execute(''' drop table articles''')
        c.execute(''' drop table users''')
        c.execute(''' drop table bookmarks''')
        conn.commit()
        conn.close()
    else:
        print('Exiting...')
