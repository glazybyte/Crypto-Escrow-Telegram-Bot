from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import time

class MySQLDatabase:
    def __init__(self, host, port, user, password, database, pool_size=5):
        
        self.engine = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
            pool_size=pool_size,
            max_overflow=5,  
            pool_pre_ping=True 
        )
       
        self.Session = sessionmaker(bind=self.engine)

    def _execute_with_retries(self, query, params=None, max_retries=5, delay=0.9):
        for attempt in range(max_retries):
            try:
                session = self.Session()
                if params:
                    result = session.execute(text(query), params)
                else:
                    result = session.execute(text(query))
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                if "Lost connection to MySQL server during query" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise
                else:
                    raise
            finally:
                pass

    def send_data_lockmanager(self, key, value):
        self._send_data("lockmanager", key, value)

    def retrieve_data_lockmanager(self, key):
        return self._retrieve_data("lockmanager", key)

    def send_data_trade(self, key, value):
        self._send_data("trade", key, value)

    def retrieve_data_trade(self, key):
        return self._retrieve_data("trade", key)

    def send_data_wallets(self, key, value):
        self._send_data("wallets", key, value)

    def retrieve_data_wallets(self, key):
        return self._retrieve_data("wallets", key)

    def send_data_wallet_checker_queue(self, key, value):
        self._send_data("wallet_checker_queue", key, value)

    def retrieve_data_wallet_checker_queue(self, key):
        return self._retrieve_data("wallet_checker_queue", key)

    def fetch_all_wallet_checker_queue(self):
        return self._fetch_all("wallet_checker_queue")

    def send_data_user_trade(self, key, value):
        self._send_data("user_trade", key, value)

    def retrieve_data_user_trade(self, key):
        return self._retrieve_data("user_trade", key)
    
    def delete_wallet_checker_queue(self, key):
        self._delete_row("wallet_checker_queue", key)

    def _send_data(self, table_name, key, value):
        value_json = json.dumps(value)
        query = f"INSERT INTO {table_name} (`key`, `value`) VALUES (:key, :value) ON DUPLICATE KEY UPDATE `value` = :value"
        self._execute_with_retries(query, {"key": key, "value": value_json})

    def _retrieve_data(self, table_name, key):
        query = f"SELECT value FROM {table_name} WHERE `key` = :key"
        result = self._execute_with_retries(query, {"key": key}).fetchone()
        if result:
            return json.loads(result[0])
        else:
            return {}

    def _fetch_all(self, table_name):
        query = f"SELECT * FROM {table_name}"
        results = self._execute_with_retries(query).fetchall()
        if results:
            data = {key: json.loads(value) for key, value in results}
            return data
        else:
            return {}

    def _delete_row(self, table_name, key):
        query = f"DELETE FROM {table_name} WHERE `key` = :key"
        self._execute_with_retries(query, {"key": key})

    def close(self):
       
        pass

