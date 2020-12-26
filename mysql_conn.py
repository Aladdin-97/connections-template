#!/usr/bin/env python

__author__ = "Aladin-29"
__license__ = "MIT"
__version__ = 1.0
__progname__ = "mysql_conn"
__status__ = "Production"

try:
    import pymysql
    from pymysql.err import Error
except ImportError:
    print("pymysql module is missing! please install it and re-run")
    print("you can install it by running # pip install pymysql")


import os
###################### LOGGING PART #####################
import logging
from utils import log_abu_settings, cleanup

LOGS_DIR = "logs"
# get the path of the module
FILE_PATH = os.path.dirname(__file__)
# join the path with the path of logsdir
LOGS_DIR_PATH = os.path.join(FILE_PATH, LOGS_DIR)
# In this case it will be /path/to/script_dir/logs

log = logging.getLogger()
#########################################################

ERR_TEMPLATE = "An exception of type {0} occurred. Arguments:\n{1!r}"


class MySQL_client:
    """MySQL Database Client"""

    def __init__(self, host, port, user, passwd, db, ssl):
        self._host = host
        self._port = port
        self._user = user
        self._passwd = passwd
        self._db = db
        self._ssl = ssl
        self._conn = self.connection
        self._cursor = self._conn.cursor()

    @property
    def connection(self):
        try:
            log.info("Connecting to the Database...")
            # REMOVE THIS LINE IN PRODUCTION
            log.debug(f"Connecting to the DB with {self.__dict__}")
            conn = pymysql.connect(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._passwd,
                db=self._db,
                ssl=self._ssl,
            )
            log.info("Connected to the Database Successfully!")
            return conn
        except Error as db_err:
            log.error(f"Database Connection Failed: {db_err}")
            raise db_err

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self._conn.commit()

    def close(self, commit=False):
        log.debug("Closing the cursor and the connection")
        if commit:
            self.commit()
        self.cursor.close()
        self._conn.close()

    def execute(self, sql, params=None):
        log.info("Executing the Query...")
        log.debug(f"Query Statement: {sql}, params: {params}")
        try:
            self.cursor.execute(sql, params or ())
            log.info(f"Query Executed Successfully!")
        except Error as exec_err:
            log.error(f"Query Execution Failed: {exec_err}")
            raise exec_err

    def fetchall(self):
        log.debug("Fetching all rows...")
        return self.cursor.fetchall()

    def fetchone(self):
        log.debug("Fetching only one row...")
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.execute(sql, params or ())
        return self.fetchall()

    def pass_params_example(self, country_param):

        params = (country_param,)
        sql_query = """select name from user db.table lower(country) = lower(%s)"""

        results = self.query(sql_query, params)
        # in case of no results return nothing
        if len(results) == 0:
            return None

        return results

    def search_data_by_pattern(self, pattern, search_type, auto_close=True):
        """Fetch data by given sql, pattern and type of search"""

        sql = "select * from db.users where"
        params = (pattern,)
        if search_type == "like":
            sql_query = f"{sql} lower(country) like lower(%s)"

        elif search_type == "in":
            # String To Tuple
            params = eval(pattern)
            # Count how many items inside to pattern,
            # in order to add placeholder '%s' to the query
            how_many_items = pattern.split(",")
            # for example, two items will be 'in (%s, %s)'
            where_in = ",".join(["%s"] * len(how_many_items))
            sql_query = f"{sql} country in ({where_in})"

        else:
            sql_query = f"{sql} lower(country) = lower(%s)"

        results = self.query(sql_query, params)
        if auto_close:
            self.close()

        return results


if __name__ == "__main__":
    # custom logging options
    log_abu_settings(
        logs_dir_path=LOGS_DIR_PATH,
        logfile=__progname__,
        console_log_level=logging.WARNING,
        file_log_level=logging.DEBUG,
    )

    CERT_DIR = "/PATH/TO/DB_CERTS"
    CONFIG = {
        "user": "USER",
        "passwd": "PASSWORD",
        "host": "YOUR DB HOST",
        "port": 3306,  # default mysql port
        "db": "DB NAME",
        "ssl": {
            "ssl_ca": f"{CERT_DIR}/ca.pem",
            "ssl_cert": f"{CERT_DIR}/client-cert.pem",
            "ssl_key": f"{CERT_DIR}/client-key.pem",
        },
    }
    sql = "SELECT * FROM DB.TABLE"
    try:
        db_conn = MySQL_client(**CONFIG)
        first_result = db_conn.query(sql)
        second_result = db_conn.pass_params_example(country_param="Italy")
        print("First query result: ", first_result)
        print("Second query results: ", second_result)
    except Error as e:
        message = ERR_TEMPLATE.format(type(e).__name__, e.args)
        log.debug(message)
        log.error(f"Problem while operating with DB: {e}")
    finally:
        db_conn.close()
    
    # CLEAN UP PROCESS, ADD DIR TO CLEAN FILES AND DIR
    paths_to_clean = ["logs"]
    log.info(f"Cleaning process to free space from dirs {paths_to_clean}")
    for path in paths_to_clean:
        cleanup(number_of_days=30, path=f"{FILE_PATH}/{path}")
