from flask import Flask
from flask_cors import CORS, cross_origin
from flask import jsonify,request, _request_ctx_stack
from __handlers__ import ResponseHandler
import os
from k8 import KubernetesJobs

app = Flask(__name__)
cors = CORS(app)

@app.route('/job/create',methods=['POST'])
@ResponseHandler
def create_job():
    args = request.get_json()
    response = KubernetesJobs().create_job(args)
    return {'response':response}

@app.route('/job/delete',methods=['GET'])
@ResponseHandler
def delete_job():
    job_id = request.args['job_id']
    response = KubernetesJobs().delete_job(job_id)
    return {'response':response}


@app.route('/job/detailed-status',methods=['GET'])
@ResponseHandler
def get_job_detailed_info():
    job_id = request.args['job_id']
    job = KubernetesJobs().get_job_detailed_status(job_id)
    if job:
        return {
            "job" : job
        }
    else:
        return {
            'error':'No job with this id is present'
        }


@app.route('/job/running_time',methods=['GET'])
@ResponseHandler
def get_job_running_time():
    job_id = request.args['job_id']
    job = KubernetesJobs().get_job_detailed_status(job_id)
    if job:
        return {
            "running_time" : job['running_time']
        }
    else:
        return {
            'error':'No job with this id is present'
        }


@app.route('/list-pods',methods=['GET'])
@ResponseHandler
def list_running_pods():
    job_id = request.args.get('job_id')
    return {
        "pods" : KubernetesJobs().list_pods(job_id)
    }


@app.route('/job/status',methods=['GET'])
@ResponseHandler
def job_status():
    job_id = request.args['job_id']
    job = KubernetesJobs().get_job_detailed_status(job_id)
    if job:
        return {
            "status" : job['status']
        }
    else:
        return {
            'error':'No job with this id is present'
        }


@app.route('/', methods=['GET'])
@cross_origin(allow_headers=['*'])
def healthlink():
    return "Welcome to labelerr kubernetes api"

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=int(os.environ.get('PORT', 8080)))

