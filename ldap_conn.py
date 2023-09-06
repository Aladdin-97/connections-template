#!/usr/bin/env python

__author__ = "Aladin-97"
__license__ = "MIT"
__version__ = 1.0
__progname__ = "ldap_conn"
__status__ = "Production"

try:
    import ldap
    from ldap.filter import escape_filter_chars
except ImportError:
    print("ldap module is missing! please install it and re-run")
    print("you can install it by running # pip install python-ldap")

import os
import sys
import logging
from utils import cleanup, config, log_abu_settings

###################### LOGGING PART #####################
LOGS_DIR = "logs"
# get the path of the module
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
# join the path with the path of logsdir
LOGS_DIR_PATH = os.path.join(FILE_PATH, LOGS_DIR)
# In this case it will be /path/to/script_dir/logs

log = logging.getLogger()
#########################################################

EVENT_TYPE = {
    "ADD": ldap.MOD_ADD,
    "DELETE": ldap.MOD_DELETE,
    "REPLACE": ldap.MOD_REPLACE,
}

ERR_TEMPLATE = "An exception of type {0} occurred. Arguments:\n{1!r}"


class LdapClient:
    """Ldap Client"""

    def __init__(self, uri, bind_dn=None, bind_passwd=None):
        self._uri = uri
        self._user = bind_dn
        self._passwd = bind_passwd
        self._conn = self.connection

    @property
    def connection(self):
        try:
            log.info("Connecting to the LDAP Server...")
            log.debug(f"Connecting with {self._uri}")
            connect = ldap.initialize(self._uri)
            # to search the object and all its descendants
            connect.set_option(ldap.OPT_REFERRALS, 0)
            if not self._user is None:
                log.warning("*** Connecting as Admin ***")
                log.debug(
                    f"Binding with {self._user}, password=**censored**of course*hehe**"
                )
                connect.simple_bind_s(self._user, self._passwd)

            log.info("Connected to the LDAP Successfully!")
            return connect
        except ldap.INVALID_CREDENTIALS:
            log.error("User or Password is wrong Dude!...Ciao")
            sys.exit(1)
        except ldap.LDAPError as e:
            message = ERR_TEMPLATE.format(type(e).__name__, e.args)
            log.debug(message)
            err_m = f"{e.args[0].get('desc')}, More Info: {e.args[0].get('info')}"
            log.error(f"LDAP Connection Failed: {err_m}")
            sys.exit(1)

    def close(self):
        log.debug("Closing the connection...")
        self._conn.unbind_s()

    def modify(self, dn, attr_name, attr_value, event_type):
        log.debug(
            f"object to modify: {dn}, event type: {event_type}, attr name: {attr_name}, attr value: {attr_value}"
        )
        try:
            attrs = [(EVENT_TYPE[event_type], attr_name, attr_value.encode("utf-8"))]
        except KeyError:
            raise ValueError(f"Event type can be only {EVENT_TYPE.keys()}")

        log.info("Modifing record on ldap with dn: {} and attrs: {}".format(dn, attrs))
        try:
            self._conn.modify_s(dn, attrs)
            log.warning("Modifing record completed succesfully!")
        except ldap.INSUFFICIENT_ACCESS:
            log.critical(
                "Insufficient Access...I See what you have tried to do... YOU NEED TO BE ADMIN HOMAN!"
            )
        except ldap.LDAPError as e:
            message = ERR_TEMPLATE.format(type(e).__name__, e.args)
            log.debug(message)
            err_m = f"{e.args[0].get('desc')}, More Info: {e.args[0].get('info')}"
            log.error(f"Problem while modifying record: {err_m}")
            
    def search(
        self, basedn, object_to_search, attributes_to_search, escape_wildchar=True
    ):
        log.debug(f"Wildchar will be escaped ? {escape_wildchar}")
        if escape_wildchar:
            object_to_search = escape_filter_chars(object_to_search)
            log.debug("Char Escaped in search value: {}".format(object_to_search))

        log.info(f"Searching {object_to_search}")
        log.debug(
            f"Searching {object_to_search} on {basedn} with attribute to retrieve {attributes_to_search}"
        )
        try:
            results = self._conn.search_s(
                basedn,
                ldap.SCOPE_SUBTREE,
                object_to_search,
                attributes_to_search,
            )
            log.debug("Search completed successfully!")
            return results
        except ldap.LDAPError as e:
            message = ERR_TEMPLATE.format(type(e).__name__, e.args)
            log.debug(message)
            err_m = f"{e.args[0].get('desc')}, More Info: {e.args[0].get('info')}"
            log.error(f"Problem while searching: {err_m}")
            return False

    def move_to_newrdn(self, object_to_move, old_branch, new_branch, del_old=False):
        """
        Refer to the docs https://www.python-ldap.org/en/python-ldap-3.3.0/reference/ldap.html?highlight=newrdn#ldap.LDAPObject.rename_s
        """
        log.info(
            f"Moving {object_to_move}, from old branch {old_branch} to the branch {new_branch}"
        )
        try:
            self._conn.rename_s(
                dn=old_branch,
                newrdn=object_to_move,
                newsuperior=new_branch,
                delold=del_old,
            )
            log.warning("Record moved into new Branch successfully!")
        except ldap.LDAPError as e:
            message = ERR_TEMPLATE.format(type(e).__name__, e.args)
            log.debug(message)
            err_m = f"{e.args[0].get('desc')}, More Info: {e.args[0].get('info')}"
            log.error(f"Failed to move: {err_m}")


if __name__ == "__main__":
    # custom logging options
    log_abu_settings(
        logs_dir_path=LOGS_DIR_PATH,
        logfile=__progname__,
        console_log_level=logging.WARNING,
        file_log_level=logging.DEBUG,
    )
    LDAP_SERVER = config.LDAP_SERVER
    BASE_DN = config.BASE_DN  # base dn to search in
    USER_BASE_DN = config.USER_BASE_DN
    LDAP_LOGIN = config.LDAP_LOGIN
    LDAP_PASSWORD = None
    OBJECT_TO_SEARCH = "uid=aladin-29"
    ATTRIBUTES_TO_RETRIEVE = ["cn", "desc"]
    conn = LdapClient(LDAP_SERVER, LDAP_LOGIN, LDAP_PASSWORD)
    result = conn.search(
        USER_BASE_DN, OBJECT_TO_SEARCH, ATTRIBUTES_TO_RETRIEVE, escape_wildchar=False
    )
    print("Search Results: ", result)
    attr_name = "cn"
    # attribute value must be bytes type
    attr_value = b"Aladin Ldap Connection"
    object_to_modify = "uid=aladin-29"
    conn.modify(object_to_modify, attr_name, attr_value, event_type="ADD")
    conn.close()

    # CLEAN UP PROCESS, ADD DIR TO CLEAN FILES AND DIR
    paths_to_clean = ["logs"]
    log.info(f"Cleaning process to free space from dirs {paths_to_clean}")
    for path in paths_to_clean:
        cleanup(number_of_days=30, path=f"{FILE_PATH}/{path}")
