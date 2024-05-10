const express = require('express')
const app = express()
var bodyParser = require('body-parser')
const { spawn } = require('child_process');
const fs = require('fs');
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
  var size='2Gi'
  var region_id='us-central1'
  var PORT=8501
  const pubSubMessage = req.body.message;
  const name = pubSubMessage.data ? Buffer.from(pubSubMessage.data, 'base64').toString().trim(): 'World';

  const value = JSON.parse(name);
  var question_id=value.quesid
  if(value.region){region_id=value.region}
  if(value.size){size=value.size}
  if(value.port){PORT=value.port}
  var labpid=value.labellerrpid 
  var image=value.image_path
  var gcsb=value.gcsb
    var gcsdir=value.gcsdir
    var modelname=value.modelname
    var modelpath=value.modelpath
    GOOGLE_APPLICATION_CREDENTIALS=process.env.GOOGLE_APPLICATION_CREDENTIALS
    console.log(GOOGLE_APPLICATION_CREDENTIALS)
    let rawdata = fs.readFileSync(GOOGLE_APPLICATION_CREDENTIALS);
    let creds = JSON.parse(rawdata);
    var account=creds.client_email
    var googlepid=creds.project_id
  const child = spawn('./cmds.sh',[googlepid,question_id,image,region_id,gcsb,gcsdir,size,modelname,modelpath,GOOGLE_APPLICATION_CREDENTIALS,account,PORT]);

  child.on('exit', function (code, signal) {
    console.log('child process exited with ' +
                `code ${code} and signal ${signal}`);
    console.log("reached");
    res.status(204).send();
  });

});
const port = process.env.PORT || 8080;
app.listen(port, () => console.log('Application listening on port ',port))