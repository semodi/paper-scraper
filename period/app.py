import time
import json
import requests
import logging
recommender_url = 'http://rec:6545/api/'
arxv_url = 'http://arxv:6540/api/'

if __name__ == '__main__':
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    while(True):
        timeout = 360
        try:
            print('Pulling new articles from arXiv...')
            r = requests.post(arxv_url + 'update', headers=headers)
            if not r.text == '{ Success }':
                timeout = 10
        except Exception as e:
            timeout = 10
        try:
            print('Indexing new articles...')
            r = requests.post(recommender_url + 'index', headers=headers)
            if not r.text == '{ Success }':
                timeout = 10
        except Exception as e:
            timeout = 10
        print('Sleeping for {} seconds'.format(timeout))
        time.sleep(timeout)
