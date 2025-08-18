import psycopg2
import psycopg2.extras
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PostgreSQLInserter:
    def __init__(self, user=None, password=None, host=None, port=None, database=None):
        # Use environment variables if parameters not provided
        self.connection = psycopg2.connect(
            user=user or os.getenv('POSTGRES_USER', 'postgres'),
            password=password or os.getenv('POSTGRES_PASSWORD'),
            host=host or os.getenv('POSTGRES_HOST', 'localhost'),
            port=port or os.getenv('POSTGRES_PORT', '5432'),
            database=database or os.getenv('POSTGRES_DB', 'mpb_stance_mining')
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def insert_many(self, table_name, data):
        """Insert multiple rows using PostgreSQL COPY or execute_values for better performance"""
        columns = ', '.join(data.columns)
        placeholders = ', '.join(['%s'] * len(data.columns))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        data_tuples = [tuple(x) for x in data.to_numpy()]
        
        try:
            # Use execute_values for better performance with PostgreSQL
            psycopg2.extras.execute_values(
                self.cursor,
                f"INSERT INTO {table_name} ({columns}) VALUES %s",
                data_tuples,
                template=None,
                page_size=1000
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def insert_one(self, table_name, data_dict):
        """Insert a single row"""
        columns = ', '.join(data_dict.keys())
        placeholders = ', '.join(['%s'] * len(data_dict))
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        try:
            self.cursor.execute(sql, list(data_dict.values()))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def upsert_many(self, table_name, data, conflict_columns):
        """Upsert (INSERT ... ON CONFLICT) for handling duplicates"""
        columns = list(data.columns)
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        conflict_str = ', '.join(conflict_columns)
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_columns])
        
        sql = f"""
        INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})
        ON CONFLICT ({conflict_str}) 
        DO UPDATE SET {update_str}
        """
        
        data_tuples = [tuple(x) for x in data.to_numpy()]
        
        try:
            psycopg2.extras.execute_values(
                self.cursor,
                sql,
                data_tuples,
                template=None,
                page_size=1000
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e

    def execute_query(self, query, params=None):
        """Execute custom query"""
        try:
            self.cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            raise e

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

if __name__ == "__main__":
    # Example usage
    try:
        with PostgreSQLInserter() as db:
            # Test connection
            result = db.execute_query("SELECT version()")
            print("PostgreSQL version:", result[0]['version'])
    except Exception as e:
        print(f"Database connection error: {e}")