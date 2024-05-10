// /home/samkiller007/Documents/labellerrprod-cloudsqlproxy.json
const gateway = require('fast-gateway')
// const express = require('express')
const config = require('./config.json')
const cors = require('cors')
var bodyParser = require('body-parser')

// const app = express()
const { checkJwt, checkScope, secureRequest, proxyPredictionRequest } = require('./handlers')
const server = gateway({
  //   server: app,
  routes: [{
    prefix: '/hello',
    target: config.routeTargets.hello,
    middlewares:[
      bodyParser.json(),
      proxyPredictionRequest
    ]
  }
  ]
  // ,
  // middlewares: [
  //   cors(),
  //   checkJwt.unless({
  //     path: [
  //       '/auth/signup/pre',
  //       '/auth/signup',
  //       '/auth/login',
  //       '/auth/domain/available',
  //       '/contact/contact_us',
  //       '/users/add'
  //     ]
  //   }),
  //   checkScope.unless({
  //     path: [
  //       '/auth/signup/pre',
  //       '/auth/signup',
  //       '/auth/login',
  //       '/auth/domain/available',
  //       '/contact/contact_us',
  //       '/users/add'
  //     ]
  //   }),
  //   secureRequest
  // ]

})

server.start(process.env.PORT || 3000)
