const unless = require('express-unless')
const config = require('./config.json')
const database = require('./db_client.js')
const axios = require('axios');
var proxy = require('express-http-proxy');

// Auth0 dependencies
var jwtWebToken = require('jsonwebtoken')
const jwt = require('express-jwt')
// const jwtAuthz = require('express-jwt-authz')
const jwksRsa = require('jwks-rsa')

// Variables required by Auth0 middleware
const AUTH0_DOMAIN = config.auth0.AUTH0_DOMAIN
const API_AUDIENCE = config.auth0.API_AUDIENCE
const ALGORITHMS = ['RS256']

// const app = express()

// Authentication middleware. When used, the
// Access Token must exist and be verified against
// the Auth0 JSON Web Key Set
const checkJwt = jwt({
    // Dynamically provide a signing key
    // based on the kid in the header and
    // the signing keys provided by the JWKS endpoint.
    secret: jwksRsa.expressJwtSecret({
        cache: true,
        // rateLimit: true,
        // jwksRequestsPerMinute: 5,
        jwksUri: `https://${AUTH0_DOMAIN}/.well-known/jwks.json`
    }),

    // Validate the audience and the issuer.
    audience: API_AUDIENCE,
    issuer: `https://${AUTH0_DOMAIN}/`,
    algorithms: ALGORITHMS
})

checkJwt.unless = unless
// Obtains the Access Token from the Authorization Header
// Returns a dict object with data containing value and valid
// containing if boolean for valid request
function getTokenAuthHeader(headers) {
    var auth = headers.authorization

    // Check if header present
    if (!auth) {
        return 'Auth header missing'
    }
    var parts = auth.split(' ')
    // Validation header
    if (parts[0].toLowerCase() !== 'bearer') {
        return { data: 'Invalid Header - Must start with bearer', valid: false }
    } else if (parts.length === 1) {
        return { data: 'Invalid header - Token not found', valid: false }
    } else if (parts.length > 2) {
        return { data: 'Invalid header - Authorization header must be Bearer token', valid: false }
    }

    var token = parts[1]

    return { data: token, valid: true }
}

// Scope middleware. When used, the
// Check is user have privilages to use
// a certain functionality
const checkScope = function (req, res, next) {
    console.log(req.body)
    // Getting token from header and validating
    var token = getTokenAuthHeader(req.headers)
    var decoded = jwtWebToken.decode(token.data)
    req.headers.email_id = decoded['https://login.labellerr.com/meta'].email_id
    return next()
}

const { google } = require('googleapis')

const auth = new google.auth.GoogleAuth({
    keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS
    // scopes: ['https://www.googleapis.com/auth/cloud-platform']
})
checkScope.unless = unless

const secureRequest = function (req, res, next) {
    auth.getIdTokenClient('32555940559.apps.googleusercontent.com').then(client => {
        client.idTokenProvider.fetchIdToken('32555940559.apps.googleusercontent.com').then(token => {
            // console.log(token)
            req.headers.Authorization = `Bearer ${token}`
            return next()
        })
    })
}


function main(client_id, project_id, ques_id, model_id) {
    return new Promise((resolve, reject) => {

        var query_stmt_list = [
            { query: `select distinct service_endpoint from model_data where model_id = (select model_id from modelmap where client_id = '${client_id}' and project_id = '${project_id}' and ques_id = '${ques_id}' and model_id = ${model_id})`, id: '23er23df' }
        ]
        database.queryCloudSql(query_stmt_list).then((value) => {
            resolve(JSON.parse(value.query_stmt_result['23er23df'])[0]['service_endpoint'])
        }, (error) => {
            reject(error)
        })

    })

}

function proxyPredictionRequest(req, res, next) {
    main(req.body.client_id, req.body.project_id, req.body.ques_id, req.body.model_id).then((value) => {
        var request_body = req.body
        axios.post(value, request_body, { headers: { "Content-Type": "application/json" } })
            .then(function (response) {
                res.send(response.data)
            })
            .catch(function (error) {
                console.log(error)
                res.send(error)
            });
    })
}

module.exports = {
    checkJwt, checkScope, secureRequest, proxyPredictionRequest
}
