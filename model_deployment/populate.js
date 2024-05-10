const config = require('./config');
const { queryCloudSql, errorHandler } = require('./db_client');


function insert_checkpoint(model_id, version, endpoint, model_loss, model_val_loss, model_metric, model_val_metric, data_type, model_type, question_id, model_algo_id, is_active) {
    return new Promise((resolve, reject) => {

        var query_stmt_list = [

            { query: `insert into models(${config.sql.model_id_column},${config.sql.version_column},${config.sql.endpoint_column}, ${config.sql.model_loss_column}, ${config.sql.model_val_loss_column}, ${config.sql.model_metric_column}, ${config.sql.model_val_metric_column}, ${config.sql.data_type_column},${config.sql.model_type_column}, ${config.sql.question_id_column}, ${config.sql.model_algo_id_column}, ${config.sql.is_active_column}) values('${model_id}', '${version}', '${endpoint}', '${model_loss}', '${model_val_loss}', '${model_metric}', '${model_val_metric}', '${data_type}', '${model_type}', '${question_id}', '${model_algo_id}', '${is_active}')`, id: 'list_latest_log_0001' }
        ]

        queryCloudSql(query_stmt_list).then((value) => {
            if (errorHandler(value).length == 0) resolve();
            else reject(errorHandler(sqlResult)[0].error);

        }, (error) => {
            reject(error)
        }).catch(error => {
            reject(error)

        })
    })

}

module.exports = { insert_checkpoint }

