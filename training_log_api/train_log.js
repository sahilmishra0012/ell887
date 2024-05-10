const config = require('./config');
const { queryCloudSql, errorHandler } = require('./db_client');


function list_latest_log(model_id) {
    return new Promise((resolve, reject) => {

        var query_stmt_list = [

            { query: `select status, description from model_train_log where ${config.sql.model_id_column}="${model_id}"  ${config.sql.version_column}="${version}"  ORDER BY created_at desc LIMIT 1`, id: 'list_latest_log_0001' }
        ]
        queryCloudSql(query_stmt_list).then((value) => {
            if (errorHandler(value).length == 0) resolve(JSON.parse(value.query_stmt_result['list_latest_log_0001']));
            else reject(errorHandler(sqlResult)[0].error);

        }, (error) => {
            reject(error)
        }).catch(error => {
            reject(error)

        })
    })

}

module.exports = { list_latest_log }