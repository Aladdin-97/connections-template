import os
import time
import shutil
import logging
from logging.handlers import RotatingFileHandler


log = logging.getLogger()
consoleHandler = logging.StreamHandler()
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def log_abu_setting(
    logs_dir_path, logfile, console_log_level=logging.INFO, file_log_level=logging.DEBUG
):
    """Set log format for file and console"""
    FILENAME = f'{logs_dir_path}/{logfile}_{time.strftime("%Y%m%d")}.log'
    # Rotate File every 1GB,max 2 backup
    logfile_handler = RotatingFileHandler(
        filename=FILENAME,
        mode="a",
        encoding="utf-8",
        maxBytes=1000000000,
        backupCount=2,
    )

    logfile_formatter = logging.Formatter(
        "%(asctime)s - %(filename)s - %(funcName)s - %(lineno)s - %(levelname)s - %(message)s",
        DATE_FORMAT,
    )
    log.setLevel(file_log_level)
    logfile_handler.setFormatter(logfile_formatter)
    # add the handlers to the log
    log.addHandler(logfile_handler)

    # logs  : print on screen
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s: %(message)s", DATE_FORMAT
    )
    consoleHandler.setLevel(console_log_level)
    consoleHandler.setFormatter(console_formatter)
    log.addHandler(consoleHandler)


def print_table(mydict):
    # for k, v in mydict.items(): print (k, v)
    print("\n")
    for key, value in mydict.items():
        if isinstance(value, list):
            for val in value:
                print("{0:>25}: {1}".format(key, val.decode("utf-8")))
        else:
            print("{0:>25}: {1}".format(key, value))
    print("\n")


def remove(path):
    """
    Remove the file or directory
    """
    if os.path.isdir(path):
        try:
            log.debug("It's a directory, removing all subdir of {}".format(path))
            shutil.rmtree(path)
        except OSError as e:
            log.warning("Unable to remove folder: {}, Reason: [{}]".format(path, e))
    else:
        try:
            log.debug("It's NOT a directory, removing {}".format(path))
            os.remove(path)
        except OSError as e:
            log.warning("Unable to remove file: {}, Reason: [{}]".format(path, e))


def cleanup(number_of_days, path):
    """
    Removes files from the passed in path that are older than or equal
    to the number_of_days
    """
    log.debug(
        "CleanUp Process has been started, i will remove all files older than [{}] days from the dir [ {} ]".format(
            number_of_days, path
        )
    )
    numdays = 86400 * int(number_of_days)
    now = time.time()
    for element in os.listdir(path):
        item = os.path.join(path, element)
        timestamp = os.path.getmtime(item)
        if now - numdays > timestamp:
            log.debug("item: {}, timestamp:{}".format(item, timestamp))
            remove(item)
    log.info("CleanUP Process has been terminated!")

class config:
    LDAP_SERVER = "ldap://localhost:390"
    BASE_DN = "dc=your-domain,dc=it"  # base dn to search in
    USER_BASE_DN = f"ou=People,{BASE_DN}"
    LDAP_LOGIN = "cn=Admin Group"
