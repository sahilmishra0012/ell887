const { queryCloudSql, errorHandler } = require('./db_client');
const config = require('./config');
const sqlQuery = `select * from model_train_log `;

function main() {
    return new Promise((resolve, reject) => {

        var query_stmt_list = [
            { query: `select * from model_train_log`, id: '23er23df' }
        ]
        queryCloudSql(query_stmt_list).then((value) => {
            resolve(JSON.parse(value.query_stmt_result['23er23df']))
        }, (error) => {
            reject(error)
        })

    })

}

console.log(main())