from flask import Flask, request, redirect, url_for, flash, jsonify
import numpy as np
import pickle as p
import json
import recommend
import logging
app = Flask(__name__)


@app.route('/api/index', methods=['POST'])
def make_index():
    try:
        recommend.create_index()
        return "{ Success }"
    except Exception as e:
        logging.error(e)
        raise e
        return "{An unknown error occured during indexing}"

@app.route('/api/recommend', methods=['POST'])
def get_recommendation():
    data = request.get_json()
    recommendation, distances, query = recommend.get_recommendations(data.get('user_id', 0),
                                                     data.get('cutoff_days', 20),
                                                     data.get('no_papers', 10),
                                                     data.get('based_on', None))

    results = {}
    results['recommendations'] = recommendation.to_dict('records')
    results['distances'] = distances.tolist()
    results['query'] = query.to_dict('records')
    return json.dumps(results)

if __name__ == '__main__':
    # recommend.create_index()
    app.run(debug=True, host='0.0.0.0',port='6545')
