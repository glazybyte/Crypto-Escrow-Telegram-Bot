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
        #print(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")
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
    def send_data_items(self, id, value):
        seller = value.pop('seller', None)
        tags = value.pop('tags', None)
        data = value

        
        self._send_data_with_merge("items", id, data, seller=seller, tags=tags)
    def send_data_txns(self, id, value):
        item_id = value.pop('item_id', None)
        buyer = value.pop('buyer', None)
        data = value
        self._send_data_with_merge("txns", id, data, item_id=item_id, buyer=buyer)

    def retrieve_data_items(self, id):
        return self._retrieve_data_with_merge("items", id)
    
    def retrieve_data_txns(self, id):
        return self._retrieve_data_with_merge("txns", id)
    
    def fetch_items_by_seller(self, seller):
        query = "SELECT id, data, seller, tags FROM items WHERE seller = :seller"
        results = self._execute_with_retries(query, {"seller": seller}).fetchall()
        if results:
            items = [
                {**json.loads(row['data']), "id": row['id'], "seller": row['seller'], "tags": row['tags']}
                for row in results
            ]
            return items
        else:
            return []
    def send_data_intervals_timeouts(self, id, type, context, cmd, next_call_at):
        self._send_data("intervals_timeouts", id, {"type": type, "context": context, "cmd": cmd, "next_call_at": next_call_at})

    def retrieve_data_intervals_timeouts(self, id):
        return self._retrieve_data("intervals_timeouts", id)
    def delete_item(self, id):
        self._delete_row("items", id)

    def delete_interval_timeout(self, id):
        self._delete_row("intervals_timeouts", id)
    def _send_data_with_merge(self, table_name, id, data, **additional_columns):
        value_json = json.dumps(data)
        columns = ', '.join(f"`{col}`" for col in additional_columns)
        values = ', '.join(f":{col}" for col in additional_columns)
        
        update_clause = ', '.join(f"`{col}` = :{col}" for col in additional_columns)
        query = f"""
            INSERT INTO {table_name} (`id`, `data`, {columns})
            VALUES (:id, :data, {values})
            ON DUPLICATE KEY UPDATE `data` = :data, {update_clause}
        """
        params = {"id": id, "data": value_json, **additional_columns}
        self._execute_with_retries(query, params)
    
    def _retrieve_data_with_merge(self, table_name, id):
        query = f"SELECT * FROM {table_name} WHERE `id` = :id"
        result = self._execute_with_retries(query, {"id": id}).first()
        if result:
            parent_dict = result._asdict()
            data_json = json.loads(parent_dict.pop('data'))
            merged_data = {**data_json, **parent_dict}
            return merged_data
        else:
            return {}
    def fetch_all_data_intervals_timeouts(self):
        return self._fetch_all("intervals_timeouts")
    def close(self):
        pass

