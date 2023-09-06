__author__ = "Aladin-97"
__license__ = "MIT"
__version__ = 2.0
__status__ = "Production"

import os
import sys
import shutil
import time
import tty
import termios
import logging
import ipaddress
import socket
from logging.handlers import RotatingFileHandler


log = logging.getLogger()
consoleHandler = logging.StreamHandler()
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def log_abu_settings(
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

    
def get_passwd(prompt="Password: ", mask="*"):

    STR_TYPE = str  # type: type
    if not isinstance(prompt, STR_TYPE):
        raise TypeError(
            "prompt argument must be a str, not %s" % (type(prompt).__name__)
        )
    if not isinstance(mask, STR_TYPE):
        raise TypeError(
            "mask argument must be a zero- or one-character str, not %s"
            % (type(prompt).__name__)
        )
    if len(mask) > 1:
        raise ValueError("mask argument must be a zero- or one-character str")

    if mask == "" or sys.stdin is not sys.__stdin__:
        # Fall back on getpass if a mask is not needed.
        import getpass as gp

        return gp.getpass(prompt)

    enteredPassword = []  # type: List[str]
    sys.stdout.write(prompt)
    sys.stdout.flush()
    while True:
        key = ord(getch())
        if key == 13:  # Enter key pressed.
            sys.stdout.write("\n")
            return "".join(enteredPassword)
        elif key in (8, 127):  # Backspace/Del key erases previous output.
            if len(enteredPassword) > 0:
                # Erases previous character.
                sys.stdout.write(
                    "\b \b"
                )  # \b doesn't erase the character, it just moves the cursor back.
                sys.stdout.flush()
                enteredPassword = enteredPassword[:-1]
        elif 0 <= key <= 31:
            # Do nothing for unprintable characters.
            # TODO: Handle Esc, F1-F12, arrow keys, home, end, insert, del, pgup, pgdn
            pass
        else:
            # Key is part of the password; display the mask character.
            char = chr(key)
            sys.stdout.write(mask)
            sys.stdout.flush()
            enteredPassword.append(char)


def getch():

    # type: () -> str
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == "\x03":
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        # print("Hey hey hey")
        sys.exit("\nCTRL ^C Recieved, Houston, we are closing ...!")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def check_connection(sftp_host, sftp_port):
    log.info("Checking sftp host and port connectivity...")
    try:
        ipaddress.ip_address(sftp_host)
    except ValueError:
        log.debug("Hostname supplied, dns will be check...")
        if not check_dns_name(sftp_host):
            return False

    if not check_ip_and_port(sftp_host, sftp_port):
        return False

    return True


def check_dns_name(host):
    try:
        ip = socket.gethostbyname(host)
        log.debug(f"Dns resolved of host: {host} as IP: {ip}")
        return True
    except socket.gaierror:
        log.critical(f"DNS Resolution Failed of host: {host}")
        return False


def check_ip_and_port(host, port):
    destination = (host, port)
    create_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = (create_socket.connect_ex(destination),)

    if not result == (0,):
        log.critical(f"Host or port not reachable: {destination}")
        create_socket.close()
        return False

    log.debug(f"Host or port reachable: {destination}")

    return True

def check_rsa_key_path(rsa_key_path):
    log.info("Checking RSA key path...")
    p = Path(rsa_key_path)

    if p.exists() and p.is_file():
        return True
    else:
        log.error("RSA key path not found")
        return False


    
    
    
class config:
    LDAP_SERVER = "ldap://localhost:390"
    BASE_DN = "dc=your-domain,dc=it"  # base dn to search in
    USER_BASE_DN = f"ou=People,{BASE_DN}"
    LDAP_LOGIN = "cn=Admin Group"
