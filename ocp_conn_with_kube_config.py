#!/usr/bin/env python

__author__ = "Aladin-97"
__license__ = "MIT"
__version__ = 1.0
__progname__ = "ocp_conn"
__status__ = "Production"

import sys
import urllib3
import ast
import json
import logging

from kubernetes.client import ApiClient, CoreV1Api
from kubernetes.config import load_kube_config
from kubernetes.stream import stream
from openshift.dynamic import DynamicClient, exceptions
from urllib3.exceptions import HTTPError


# COMMENT IF YOU USE VERIFIED CERTFICATE
urllib3.disable_warnings()
# Disable warnings for connectionpool
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)


def _print(msg, debug=False):
    if debug:
        print(msg)


def _get_error_message(msg, e, debug):
    try:
        error = ast.literal_eval(e.body.decode("utf-8"))
        _print(msg.format(json.dumps(error, indent=4)), debug)
    except Exception:
        _print(msg.format(e), debug)


class oc_connection:
    """OC connection driver"""

    def __init__(self, kube_config_file, namespace, api_version="v1", kind="Pod", debug=False):
        self.debug = debug
        self.namespace = namespace
        try:
            _print(f"# Loading kube config file: {kube_config_file}", debug)
            self.kube_config_file = load_kube_config(config_file=kube_config_file)
        except Exception as e:
            _print(f"# Failed to load kube config file: {e}", debug)
            print(json.dumps({"OCP Connection Status": "Failed to load config"}, indent=4))
            sys.exit(1)

        self.conn = self.connection
        if not self.conn:
            print(
                json.dumps(
                    {"OCP Connection Status": "Failed to connect to the OCP cluster"},
                    indent=4,
                )
            )
            sys.exit(1)

        self.resources = self.conn.resources.get(api_version=api_version, kind=kind)

    @property
    def connection(self):
        try:
            _print("# Connecting to the OC...", self.debug)
            k8s_client = ApiClient(self.kube_config_file)
            dyn_client = DynamicClient(k8s_client)
            _print("# Connected to OC", self.debug)
            return dyn_client

        except HTTPError as conn_error:
            _print(
                f"# Connection Error...Failed to connect to the OC: {conn_error}",
                self.debug,
            )
            return False
        except Exception as error:
            msg = "# Something went wrong while connecting to the OC cluster: {}"
            _get_error_message(msg, error, self.debug)
            return False


    def list_all_objects(self):
        try:
            obj_list = self.resources.get(namespace=self.namespace)
            _print(f"# Found {len(obj_list.items)} objects in the namespace {self.namespace}")
            for obj in obj_list.items:
                _print(f"# Object: {obj.metadata.name} status: {obj.status.phase}")
            return True
        except HTTPError as conn_error:
            _print(
                f"# Connection Error...Failed to list all objects: {conn_error}",
                self.debug,
            )
            return False
        except Exception as error:
            msg = "# Something went wrong while listing all objects: {}"
            _get_error_message(msg, error, self.debug)
            return False

    def get_object(self, obj_name):
        try:
            _print(f"# Getting object name {obj_name}", self.debug)
            obj_instance = self.resources.get(name=obj_name, namespace=self.namespace)
            return obj_instance
        except exceptions.NotFoundError as error:
            _print(f"# Object [{obj_name}] not found", self.debug)
            return False
        except HTTPError as conn_error:
            _print(f"# Connection Error...Failed to get object: {conn_error}", self.debug)
            return False
        except Exception as error:
            _print(f"# Something went wrong while getting object: {obj_name}", self.debug)
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False

    ##########################################################
    #                     POD SECTION                        #
    ##########################################################
    def create_pod(self, pod_name, pod_spec):
        try:
            _print(f"# Creating pod {pod_name}", self.debug)
            pod_instance = self.resources.create(body=pod_spec, namespace=self.namespace)
            _print(f"# Created pod [{pod_name}]", self.debug)
            return pod_instance
        except exceptions.ConflictError:
            _print(f"# Pod [{pod_name}] already exists", self.debug)
            _print("# Checking Pod status...", self.debug)
            pod_instance = self.get_object(pod_name)
            if pod_instance and pod_instance.status.phase == "Running":
                _print(
                    f"# An instance of pod [{pod_name}] is running...skipping the creation of pod!",
                    self.debug,
                )

                return False
            else:
                _print(f"# No Running pod [{pod_name}] found...", self.debug)
                pod_instance = self.delete_pod(pod_name, recreate=True, pod_spec=pod_spec)

            return pod_instance

        except HTTPError as conn_error:
            _print(f"# Connection Error...Failed to create pod: {conn_error}", self.debug)
            return False
        except Exception as error:
            _print(f"# Something went wrong while creating pod: {pod_name}", self.debug)
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False

    def delete_pod(self, pod_name, recreate=False, pod_spec=None):
        try:
            _print(f"# Deleting pod {pod_name}", self.debug)
            pod_instance = self.resources.delete(name=pod_name, namespace=self.namespace)
            _print(f"# Deleted pod [{pod_name}]", self.debug)
            if recreate:
                _print(f"# Recreating pod {pod_name}", self.debug)
                pod_instance = self.create_pod(pod_name, pod_spec)
                _print(f"# Recreated pod [{pod_name}]", self.debug)
            return pod_instance
        except HTTPError as conn_error:
            _print(f"# Connection Error...Failed to delete pod: {conn_error}", self.debug)
            return False
        except Exception as error:
            _print(f"# Something went wrong while deleting pod: {pod_name}", self.debug)
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False

    def exec_inside_pod(self, pod_name, exec_command):

        try:
            _print(f"# Executing command {exec_command} inside pod {pod_name}", self.debug)
            api_instance = CoreV1Api(self.kube_config_file)
            exec_result = stream(
                api_instance.connect_get_namespaced_pod_exec,
                pod_name,
                self.namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            return exec_result
        except HTTPError as conn_error:
            _print(
                f"# Connection Error...Failed to execute command inside pod: {conn_error}",
                self.debug,
            )
            return False
        except Exception as error:
            _print(
                f"# Something went wrong while exec command inside pod: {pod_name}",
                self.debug,
            )
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False

    ##########################################################
    #                     CRONJOB SECTION                    #
    ##########################################################

    def create_cronjob(self, cronjob_name, cronjob_spec):
        try:
            _print(f"# Creating cronjob {cronjob_name}", self.debug)
            self.resources.create(body=cronjob_spec, namespace=self.namespace)
            _print(f"# Created cronjob [{cronjob_name}]", self.debug)
            return True
        except exceptions.ConflictError:
            _print(
                f"# Cronjob [{cronjob_name}] already exists...skipping this!",
                self.debug,
            )
            return False
        except HTTPError as conn_error:
            _print(
                f"# Connection Error...Failed to create cronjob: {conn_error}",
                self.debug,
            )
            return False
        except Exception as error:
            _print(
                f"# Something went wrong while creating cronjob: {cronjob_name}",
                self.debug,
            )
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False

    def delete_cronjob(self, cronjob_name):
        try:
            _print(f"# Deleting cronjob {cronjob_name}", self.debug)
            cronjob_instance = self.resources.delete(name=cronjob_name, namespace=self.namespace)
            _print(f"# Deleted cronjob [{cronjob_name}]", self.debug)
            return cronjob_instance.to_dict()
        except HTTPError as conn_error:
            _print(
                f"# Connection Error...Failed to delete cronjob: {conn_error}",
                self.debug,
            )
            return False
        except Exception as error:
            _print(
                f"# Something went wrong while deleting cronjob: {cronjob_name}",
                self.debug,
            )
            _get_error_message("# Possible Reason: {}", error, self.debug)
            return False
