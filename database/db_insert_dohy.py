import pymysql
import pandas as pd

class MySQLInserter:
    def __init__(self, user, password, host, port, database):
        self.connection = pymysql.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.connection.cursor()

    def insert_many(self, table_name, data):
        columns = ', '.join(data.columns)
        placeholders = ', '.join(['%s'] * len(data.columns))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        data_tuples = [tuple(x) for x in data.to_numpy()]
        self.cursor.executemany(sql, data_tuples)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

if __name__ == "__main__":
    pass