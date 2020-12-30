from flask import Flask, request, redirect, url_for, flash, jsonify
import numpy as np
import pickle as p
import json
import recommender

app = Flask(__name__)


@app.route('/api/index/', methods=['POST'])
def make_index():
    recommender.create_index()
    return "{success}"

@app.route('/api/recommend/', methods=['POST'])
def get_recommendation():
    data = request.get_json()
    recommendation = recommender.get_recommendations(data.get('user_id', 0),
                                                     data.get('cutoff_days', 20),
                                                     data.get('no_papers', 10))

    return json.dumps(recommendation.to_dict('records'))

if __name__ == '__main__':
    recommender.create_index()
    app.run(debug=True, host='0.0.0.0',port='6545')
