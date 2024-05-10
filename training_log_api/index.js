'use strict';
const express = require('express');
var cors = require('cors')
var app = express()
app.use(cors())
const port = process.env.PORT || 8080;

const bodyParser = require('body-parser');

const config = require('./config');
const  logs  = require('./train_log');
app.use(bodyParser.json())
app.post('/train/logs', (req, res) => {
    try {
        const model_id = req.body.model_id;
        logs.list_latest_log(model_id)
            .then((resp) => {
                res.json(resp);
            }).catch(error => {
                res.status(400).json({ error:error.message })
            })
    } catch (error) {
        res.status(400).json({ error:error.message })
    }
});

app.listen(port, () => console.log(`Logs app listening on port ${port}!`))