from flask import jsonify
from functools import update_wrapper
from flask import request

import logging
import jwt
import json
import base64
logging.basicConfig(level=logging.INFO)

__all__  = ['ResponseHandler']

class ResponseHandler:
    def __init__(self, function):
        update_wrapper(self, function)
        self.function = function
        
    def __name__(self):
        return 'ResponseHandler'

    def __call__(self, *args, **kwargs):
        try:
            response = self.function(*args, **kwargs)
            return self.success(response)

        except Exception as err:
            logging.exception(err)
            return self.error(str(err))

    def success(self, _json=None):
        json = {
            "response": _json if _json else "success" 
        }
        return jsonify(json), 200

    def error(self, _json=None, status_code=400):
        json = {
            "error": _json if _json else "Unknown Error" 
        }
        return jsonify(json), status_code