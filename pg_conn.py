import logging
import psycopg2


log = logging.getLogger(__name__)
ERR_TEMPLATE = "An exception of type {0} occurred. Arguments: {1!r}"


class PostgresClient:
    def __init__(
        self,
        postgres_host,
        postgres_port,
        postgres_user,
        postgres_password,
        postgres_db,
    ):
        self._host = postgres_host
        self._port = postgres_port
        self._user = postgres_user
        self._passwd = postgres_password
        self._db = postgres_db
        # self._ssl = ssl
        self._conn = self.connection
        if self._conn:
            self._cursor = self._conn.cursor()

    @property
    def connection(self):
        try:
            log.info("Trying to connect to Database...")
            conn = psycopg2.connect(
                user=self._user,
                password=self._passwd,
                host=self._host,
                port=self._port,
                database=self._db,
            )
            log.info("Connected to the Database successfully!")
            return conn
        except psycopg2.Error as error:
            log.error(f"Database Connection Failed: {error}")

        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False

    @property
    def cursor(self):
        return self._cursor

    def close(self):
        log.debug("Closing the cursor and the connection...")
        self.cursor.close()
        self._conn.close()

    def rollback(self):
        # If an exception occurs while executing an SQL statement you need to call the connection's rollback method
        # to reset the transaction's state.
        # PostgreSQL will not permit further statement execution otherwise.
        log.debug("Resetting the connection cursor")
        self._conn.rollback()

    def execute(self, sql):
        log.info(f"Executing the Query: '{sql}'")
        log.debug(f"Query Statement: {sql}")

        try:
            self.cursor.execute(sql)
            log.info(f"Query Executed Successfully!")
            return True
        except psycopg2.Error as exec_err:
            log.error(f"Query Execution Failed: {exec_err}")
            self.rollback()
        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False

    def fetchall(self):
        log.debug("Fetching all rows...")
        try:
            return self.cursor.fetchall()
        except psycopg2.Error as error:
            log.error(f"Problem while operating with DB: {error}")
        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False
