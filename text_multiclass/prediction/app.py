'''
Flask API to make predictions
'''
import logging
import os
from flask import Flask
from flask_cors import CORS, cross_origin
from flask import request
import prediction
import time
import json, os
from __handlers__ import ResponseHandler

app = Flask(__name__)
cors = CORS(app)


@app.route('/v1/models/predict', methods=['POST'])
@ResponseHandler
def get_predictions():

    '''Function to call when a POST request is made.

        Parameters:
            None
        Return Value:
            Predictions List.
    '''

    if request.method == 'POST':
        json_data = request.get_json()     
        model_path = json_data['model_path']
        data = prediction.load_preprocess_data(json_data)
        print("Downloading Model")
        status = prediction.download_and_load_model(model_path)
        print(status)
        return prediction.predict_on_data(data)


port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port, debug=True)
