import socket
import paramiko
import logging
import utils as ut

log = logging.getLogger(__name__)
ERR_TEMPLATE = "An exception of type {0} occurred. Arguments: {1!r}"


class SFTPConnectionManager:
    def __init__(self, sftp_host, sftp_port, username, private_key_path, password=None):
        self.sftp_host = sftp_host
        self.port = sftp_port
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None

    def login(self, timeout=30):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        log.info(f"Connecting to the host: {self.sftp_host}")

        if not ut.check_connection(self.sftp_host, self.port):
            return False
        try:
            if self.private_key_path:
                if not ut.check_rsa_key_path(config.SFTP_PRIVATE_KEY_PATH):
                    return False
                private_key = paramiko.RSAKey.from_private_key_file(
                    self.private_key_path
                )
                client.connect(
                    hostname=self.sftp_host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False,
                )
            else:
                client.connect(
                    self.sftp_host,
                    self.port,
                    self.username,
                    self.password,
                    timeout=timeout,
                )

            log.info(f"SFTP Connection successfull to the host: {self.sftp_host}")
            self.client = client
            return True

        except paramiko.AuthenticationException as e:
            log.error(f"SFTP Authentication Failed: {e}")

        except paramiko.SSHException as e:
            log.error(f"SSH2 protocol negotiation or logic errors: {e}")

        except socket.timeout as e:
            log.error(f"SFTP Connection error {e}")

        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False

    def logout(self):
        if self.client:
            self.client.close()
            log.info("SFTP Connection closed.")
            self.client = None
        else:
            log.info("No connection to close.")

    def copy_file(self, source_path, destination_path):
        if self.client is None:
            log.info("SFTP Not connected.")
            return False

        sftp = self.client.open_sftp()
        try:
            sftp.put(source_path, destination_path)
            log.info(f"File exported from {source_path} to {destination_path}")
            return True
        except Exception as e:
            log.error(f"Error exporting file: {e}")
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))
            return False

        finally:
            sftp.close()

    def list_files(self, remote_path):
        if self.client is None:
            log.info("SFTP Not connected.")
            return

        sftp = self.client.open_sftp()
        try:
            file_list = sftp.listdir(remote_path)
            log.info(f"Files in remote directory: {file_list}")
        except Exception as e:
            log.info(f"Error listing files: {e}")
        finally:
            sftp.close()

    # function not used, only for testing purpose
    def delete_file(self, remote_path):
        if self.client is None:
            log.info("SFTP Not connected.")
            return

        sftp = self.client.open_sftp()
        try:
            sftp.remove(remote_path)
            log.info(f"File deleted: {remote_path}")
        except Exception as e:
            log.info(f"Error deleting file: {e}")
        finally:
            sftp.close()


if __name__ == "__main__":
    ## testing purpose ##
    # run fake sftp with:
    # docker run -p 2222:22 -d atmoz/sftp user:passwd:::upload
    sftp_connection = SFTPConnectionManager("localhost", 2222, "user", "passwd")
    sftp_connection.login()
    sftp_connection.copy_file(
        "/app/app.py",
        "/upload/app.py",
    )
    sftp_connection.list_files("/upload")
    sftp_connection.delete_file("/upload/app.py")
    sftp_connection.list_files("/upload")
    sftp_connection.logout()
