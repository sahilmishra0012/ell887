import pymysql

class CloudSQLDB:
    def __init__(self, user, password, db):
        self.user = user
        self.password = password
        self.db = db

    def create_connection(self):
        return pymysql.connect(user=self.user, password=self.password, db=self.db)

    def write_labels(self, db, model_id, label, label_id, label_position):
        cursor = db.cursor()
        sql = 'insert into model_labels(model_id, label, label_id, label_position) values ("{}","{}","{}",{})'.format(model_id, label, label_id, label_position)
        cursor.execute(sql)
        db.commit()

    def write_logs(self, db, model_id, status, description, job_id):
        cursor = db.cursor()
        sql = 'insert into model_train_log(model_id, status, description, job_id) values ("{}","{}","{}","{}")'.format(model_id, status, description, job_id)
        cursor.execute(sql)
        db.commit()

    def show_labels(self, db):
        cursor = db.cursor()
        sql = 'select * from model_labels'
        cursor.execute(sql)
        results = cursor.fetchall()
        return results

    def disconnect(self, db):
        db.close()
