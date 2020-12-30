import arxiv
import pymysql
import pandas as pd
import datetime
import time
import sys
import mysql_config

if __name__ == '__main__':
    conn = pymysql.connect(mysql_config.host,
                           user=mysql_config.name,
                           passwd=mysql_config.password,
                           connect_timeout=5,
                           port=mysql_config.port)
    c = conn.cursor()
    c.execute(''' create database arxiv''')
    conn.commit()
    conn.close()
