
from tinydb import TinyDB, Query
from functools import wraps
import logging

log = logging.getLogger(__name__)
ERR_TEMPLATE = "An exception of type {0} occurred. Arguments: {1!r}"


def require_table_selected(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.table is not None:
            return func(self, *args, **kwargs)
        else:
            raise ValueError(
                "No table selected. Use use_table() method to select a table."
            )

    return wrapper


class AppDbClient:
    def __init__(self, db_name):
        self.db = TinyDB(db_name)
        self.table = None

    def use_table(self, table_name):
        log.debug("Selecting current table...")
        self.table = self.db.table(table_name)

    def close(self):
        log.debug("Closing connection to database")
        return self.db.close()

    @require_table_selected
    def insert(self, dictionary_data):
        log.debug("Inserting new record in the table")
        return self.table.insert(dictionary_data)


    @require_table_selected
    def update_data_sql_query(self, id, update_data_dictionary):
        log.debug("Updating sql_query column in a table's record")
        self.table.update(update_data_dictionary, Query().id == id)


    @require_table_selected
    def drop_table(self, table):
        try:
            log.debug(f"Dropping table: {table}")
            self.db.drop_table(table)
        except Exception as e:
            log.debug(ERR_TEMPLATE.format(type(e).__name__, e.args))
