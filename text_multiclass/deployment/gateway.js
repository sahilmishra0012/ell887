// The package @grpc/grpc-js can also be used instead of grpc here
const grpc = require('grpc')
const protoLoader = require('@grpc/proto-loader')
const { GoogleAuth } = require('google-auth-library')

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

async function queryCloudSql (serverAddress, queries, plaintext) {
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
      // const googleCreds = await new GoogleAuth().getApplicationDefault();
      const auth = new GoogleAuth()

      auth.getIdTokenClient('32555940559.apps.googleusercontent.com').then(client => {
        client.idTokenProvider.fetchIdToken('32555940559.apps.googleusercontent.com').then(token => {
        //   console.log(token)
          const cloudsql = new cloudsqlProto.CloudSql(serverAddress, credentials)
          const request = {
            query_stmt_list: queries
          }
          var metadata = new grpc.Metadata()
          metadata.add('Authorization', `Bearer ${token}`)
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

function main () {
  var query_stmt_list = [
    { query: 'select email_id from client_projects_users limit 10', id: '23er23df' }
    // { query: 'select email_id from client_projects_users limit 200', id: '23er23sdff' }
  ]
  queryCloudSql('cloudsqlservice-ca25pynkyq-uc.a.run.app', query_stmt_list, false).then((value) => {
    console.log('so')
    console.log(value.query_stmt_result)
  }, (error) => {
    console.log('er')
    console.error(error)
  })
}

main()