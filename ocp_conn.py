#!/usr/bin/env python
__author__ = "Aladin-97"
__license__ = "MIT"
__version__ = 1.0
__progname__ = "ocp_conn"
__status__ = "Production"
"""
An Openshift connection driver which can use service account token mounted on pod or user and password to connect to the Openshift via API.
"""
from kubernetes import client, config
from kubernetes.dynamic.exceptions import ForbiddenError
from openshift.dynamic import DynamicClient, exceptions
from openshift.helper.userpassauth import (
    OCPLoginConfiguration,
    OCPLoginRequestException,
)
from urllib3.exceptions import HTTPError
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)
ERR_TEMPLATE = "An exception of type {0} occurred. Arguments: {1!r}"


class OCPConnectionManager:
    """OC connection driver"""

    def __init__(
        self,
        api_url,
        username,
        passwd,
        enable_service_account=True,
        verify_ssl=False,
        ssl_ca_cert=None,
        ocp_debug=False,
    ):
        self.api_url = api_url
        self.username = username
        self.passwd = passwd
        self.enable_sa = enable_service_account
        self.verify_ssl = verify_ssl
        self.ssl_ca_cert = ssl_ca_cert
        self.debug = ocp_debug
        self.conn = self.connection
        if not self.conn:
            raise Exception("Failed to connect to the OCP cluster")

    @property
    def connection(self):
        log.debug("Connecting to the Openshift Cluster...")

        try:
            if self.enable_sa:
                log.info("Using Service Account of The Pod to Access OCP Cluster")
                config.load_incluster_config()
                log.debug("Creating api cliente interface..")
                k8s_client = client.ApiClient()

            else:
                log.info("Using User and Password to Access OCP Cluster")
                kubeConfig = OCPLoginConfiguration(
                    ocp_username=self.username, ocp_password=self.passwd
                )
                kubeConfig.host = self.api_url
                kubeConfig.verify_ssl = self.verify_ssl
                kubeConfig.debug = self.debug
                # './ocp.pem' use a certificate bundle for the TLS validation
                kubeConfig.ssl_ca_cert = self.ssl_ca_cert
                kubeConfig.get_token()
                log.debug(f"OC Login Token will expire in {kubeConfig.api_key_expires}")
                log.debug("Creating api cliente interface..")
                k8s_client = client.ApiClient(kubeConfig)

            dyn_client = DynamicClient(k8s_client)
            log.info(f"Connected to the Openshift Cluster via url: {self.api_url}")
            return dyn_client

        except HTTPError as conn_error:
            log.error(
                f"Connection Error...Failed to connect to the OC: {conn_error}",
            )
        except OCPLoginRequestException as e:
            log.error(f"Error while authenticating: {e}")

        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False

    @property
    def ocp(self):
        return self.conn.resources

    def list_all_objects(self, api_version, kind, namespace=None):
        try:
            objects = self.ocp.get(api_version=api_version, kind=kind)
            object_list = objects.get(namespace=namespace)
            for item in object_list.items:
                log.debug(item.metadata.name)
            return True
        except exceptions.NotFoundError as e:
            log.error(f"Object [{e}] not found")

        except exceptions.ResourceNotFoundError as e:
            log.error(e)
        except HTTPError as conn_error:
            log.error(f"Connection Error...Failed to list all objects: {conn_error}")
        except ForbiddenError as e:
            log.error(f"Request Forbidden for resource {kind}")
        except Exception as e:
            log.exception(ERR_TEMPLATE.format(type(e).__name__, e.args))

        return False


if __name__ == "__main__":
    api = "https://api.okd.clustername.local:6443"
    user = ""
    passwd = ""
    conn = OCPConnectionManager(api, user, passwd)
    conn.list_all_objects("v1", "Pod")
