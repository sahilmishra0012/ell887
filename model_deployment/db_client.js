// The package @grpc/grpc-js can also be used instead of grpc here
const grpc = require('grpc')
const protoLoader = require('@grpc/proto-loader')
const { GoogleAuth } = require('google-auth-library')
const config = require('./config.json')
const packageDefinition = protoLoader.loadSync(
  `${__dirname}/cloudsql.proto`,
  {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
  })
const cloudsqlProto = grpc.loadPackageDefinition(packageDefinition)
grpc.credentials.createFromGoogleCredential()

async function queryCloudSql(queries, plaintext = false, serverAddress = config.grpc_db_address) {
  return new Promise((resolve, reject) => {
    let credentials
    if (plaintext) {
      credentials = grpc.credentials.createInsecure()
      const cloudsql = new cloudsqlProto.CloudSql(serverAddress, credentials)
      const request = {
        query_stmt_list: queries
      }
      cloudsql.QueryCloudSql(request, (error, response) => {
        if (error) {
          reject(error)
        } else {
          resolve(response)
        }
      })
    } else {
      credentials = grpc.credentials.createSsl()
      /** Google Auth */
      const auth = new GoogleAuth()
      /**
      * Fetches ID Token required to authenticate with cloud run service
      */
      auth.getIdTokenClient('32555940559.apps.googleusercontent.com').then(client => {
        client.idTokenProvider.fetchIdToken('32555940559.apps.googleusercontent.com').then(token => {
          //   console.log(token)
          const cloudsql = new cloudsqlProto.CloudSql(serverAddress, credentials)
          const request = {
            query_stmt_list: queries
          }
          /** Adding Auth headers to grpc request */
          var metadata = new grpc.Metadata()
          metadata.add('Authorization', `Bearer ${token}`)
          /** gRPC request */
          cloudsql.QueryCloudSql(request, metadata, (error, response) => {
            if (error) {
              reject(error)
            } else {
              resolve(response)
            }
          })
        })
      })
    }
  })
}
/**
 * Parses and throws known and defined error from queries
 * You can define and configure your custom errors here.
 * @param {object} result
 */
function errorHandler(result) {
  return Object.keys(result.query_stmt_result).map(key => {
    const resultInside = JSON.parse(result.query_stmt_result[key])
    console.log(resultInside)
    if (resultInside.errno) {
      /** Return custom error */
      return {
        error: config.error_codes[String(resultInside.errno)],
        result: null
      }
    } else {
      return {
        result: resultInside,
        id: key
      }
    }
  }).filter(e => e.error)
}

module.exports = { queryCloudSql, errorHandler }
