const express = require('express')
const app = express()
var bodyParser = require('body-parser')
const { GoogleAuth } = require('google-auth-library');
const fs = require('fs');
const { insert_checkpoint } = require('./populate')

app.use(bodyParser.json());
app.post('/deploy', (req, res) => {
	if (!req.body) {
		const msg = 'no Pub/Sub message received';
		console.error(`error: ${msg}`);
		res.status(400).send(`Bad Request: ${msg}`);
		return;
	}
	if (!req.body.message) {
		const msg = 'invalid Pub/Sub message format';
		console.error(`error: ${msg}`);
		res.status(400).send(`Bad Request: ${msg}`);
		return;
	}

	const pubSubMessage = req.body.message;
	const name = pubSubMessage.data ? Buffer.from(pubSubMessage.data, 'base64').toString().trim() : 'World';

	var currentDate = new Date();
	var date = currentDate.getDate();
	var month = currentDate.getMonth(); //Be careful! January is 0 not 1
	var year = currentDate.getFullYear();
	var timestamp = currentDate.getTime();
	var dateString = date + "-" + (month + 1) + "-" + year + "-" + timestamp;

	const value = JSON.parse(name);
	var question_id = value.quesid
	var revisionName = ("ml-"+question_id + "-" + dateString).toLowerCase();
	revisionName = revisionName.substring(0,60)

	var size = '2Gi'
	var region_id = 'us-central1'
	var PORT = 8080

	if (value.region) { region_id = value.region }
	if (value.size) { size = value.size }
	if (value.port) { PORT = value.port }
	var image = value.image_path
	var gcsb = value.gcsb
	var gcsdir = value.gcsdir
	var modelname = value.modelname
	var modelpath = value.modelpath
	var client_project_id = value.project_id
	var model_id = value.model_id
	var algorithm_id = value.model_algorithm_id
	var region_endpoint = region_id + "-run.googleapis.com"
	var loss = value.loss
	var val_loss = value.val_loss
	var metric = value.metric
	var val_metric = value.val_metric
	var data_type = value.data_type
	var model_type = value.model_type

	GOOGLE_APPLICATION_CREDENTIALS = "autolabel-287715-bff75ec03073.json"
	let rawdata = fs.readFileSync(GOOGLE_APPLICATION_CREDENTIALS);
	let creds = JSON.parse(rawdata);
	var account = creds.client_email
	var project_id = creds.project_id
	var is_active = "Active";


	json_data = {
		"status": {
			"latestReadyRevisionName": `${revisionName}`,
			"traffic": [
				{
					"latestRevision": true,
					"percent": 100,
					"revisionName": `${revisionName}`
				}
			],
			"latestCreatedRevisionName": `${revisionName}`
		},
		"kind": "Service",
		"spec": {
			"traffic": [
				{
					"latestRevision": true,
					"percent": 100
				}
			],
			"template": {
				"spec": {
					"containers": [
						{
							"image": `${image}`,
							"resources": {
								"limits": {
									"cpu": "1000m",
									"memory": `${size}`
								}
							},
							"env": [
								{
									"name": "gcs_bucket",
									"value": `${gcsb}`
								},
								{
									"name": "gcs_subdir",
									"value": `${gcsdir}`
								},
								{
									"name": "MODEL_NAME",
									"value": `${modelname}`
								},
								{
									"name": "MODEL_BASE_PATH",
									"value": `${modelpath}`
								}
							],
							"ports": [
								{
									"containerPort": PORT
								}
							]
						}
					],
					"timeoutSeconds": 900,
					"containerConcurrency": 80
				},
				"metadata": {
					"name": `${revisionName}`,
					"annotations": {
						"run.googleapis.com/client-name": "gcloud",
						"client.knative.dev/user-image": `${image}`,
						"autoscaling.knative.dev/maxScale": "1000",
						"run.googleapis.com/client-version": "302.0.0"
					}
				}
			}
		},
		"apiVersion": "serving.knative.dev/v1",
		"metadata": {
			"name": `${revisionName}`,
			"generation": 254,
			"labels": {
				"cloud.googleapis.com/location": `${region_id}`
			},
			"annotations": {
				"run.googleapis.com/client-name": "gcloud",
				"client.knative.dev/user-image": `${image}`,
				"serving.knative.dev/creator": `${account}`
			}
		}
	}


	var post_url = `https://${region_endpoint}/apis/serving.knative.dev/v1/namespaces/${project_id}/services`
	var get_url = `https://${region_endpoint}/apis/serving.knative.dev/v1/namespaces/${project_id}/services/${revisionName}`

	async function create_service() {
		return new Promise(async (resolve, reject) => {
			const auth = new GoogleAuth({
				keyFile: "autolabel-287715-bff75ec03073.json",
				scopes: 'https://www.googleapis.com/auth/cloud-platform'
			});

			var post_request = {
				method: 'post',
				data: json_data,
				url: post_url
			}

			const client = await auth.getClient();
			const projectId = auth.getProjectId();
			const res = await client.request(post_request,
				function (err, res, body) {
					if (err) {
						reject(err)
					}
					else {
						resolve("Service Deployed. Getting Endpoint")
					}
				});

		})
	}

	async function get_service_url() {
		return new Promise(async (resolve, reject) => {
			const auth = new GoogleAuth({
				keyFile: "autolabel-287715-bff75ec03073.json",
				scopes: 'https://www.googleapis.com/auth/cloud-platform'
			});

			var get_request = {
				method: 'get',
				url: get_url
			}
			const client = await auth.getClient();
			const projectId = await auth.getProjectId();
			var url;
			var count = 0;
			do {
				const result = await x();
				const uri = client.request(get_request,
					function (err, res, body) {
						if (err) {
							reject('error posting json:' + err)
						}
						url = res.data['status']['url']
					});
				count++;
			} while (url == null && count <= 10);
			if (url == null) {
				reject('URL not Found')
			}
			else {
				console.log('Inserting values to db')
				insert_checkpoint(model_id, modelpath, url, loss, val_loss, metric, val_metric, data_type, model_type, question_id, algorithm_id, is_active)
				resolve('Endpoint ' + url + ' Pulled. DB Table Populated')
			}
		})
	}

	function x() {
		var promise = new Promise(function (resolve, reject) {
			setTimeout(function () {
				resolve('done!');
			}, 10000);
		});
		return promise;
	}


	create_service().then(async function (response) {
		console.log(response)
		const result = await x();
		get_service_url().then(function (url_response) {
			console.log(url_response)
		}).catch(function (err) { console.error("Get Service Error=>",err) })
	}).catch(function (error) { console.error("Create Service Error=>",error) })
	res.status(204).send();
	console.log('Acknowledging Receipt')
	return
});
const port = process.env.PORT || 8080;
app.listen(port, () => console.log('Application listening on port ', port))
