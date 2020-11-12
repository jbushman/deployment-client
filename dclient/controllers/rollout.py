import os
from flask import request
from dclient.util.config import Config
from dclient.util.http_helper import get_http
from dclient.util.core import (
    get_yum_transaction_id,
    install_pkgs,
    restart_service,
    get_installed,
)


def post_rollout():
    data = request.get_json()

    payload = {
        "hostname": Config.DEPLOYMENT_CLIENT_HOSTNAME,
        "state": "UPDATING",
    }
    http = get_http()
    http.patch(f"{Config.DEPLOYMENT_API_URI}/server", json=payload)

    try:
        for pkg in data["versionlock"]:
            stat = os.system(f"sudo yum versionlock add {pkg}")
            if stat != 0:
                raise Exception(stat)
        if not get_installed("httpd"):
            data["versionlock"].append("httpd")
        if not get_installed("mod_perl"):
            data["versionlock"].append("mod_perl")
        install_pkgs(data["versionlock"])
        yum_transaction_id = get_yum_transaction_id()
        yum_rollback_id = yum_transaction_id - 1
        if "buildall" in data:
            stat = os.system("sudo /var/hp/common/bin/buildall -s")
            if stat != 0:
                raise Exception(stat)
        restart_service("httpd.service")
        stat = os.system("systemctl status httpd.service")
        if stat != 0:
            raise Exception(stat)

        payload = {
            "deployment_id": int(data["deployment_id"]),
            "action": "Update",
            "state": "SUCCESS",
            "output": "deployment was successful",
            "yum_transaction_id": yum_transaction_id,
            "yum_rollback_id": yum_rollback_id,
        }
        http = get_http()
        http.post(
            f"{Config.DEPLOYMENT_API_URI}/server/history/{Config.DEPLOYMENT_CLIENT_HOSTNAME}",
            headers=headers,
            json=payload,
        )

        payload = {
            "hostname": Config.DEPLOYMENT_CLIENT_HOSTNAME,
            "state": "ACTIVE",
        }
        http = get_http()
        http.patch(f"{Config.DEPLOYMENT_API_URI}/server", json=payload)

        response = {
            "protocol": Config.DEPLOYMENT_CLIENT_PROTOCOL,
            "hostname": Config.DEPLOYMENT_CLIENT_HOSTNAME,
            "port": Config.DEPLOYMENT_CLIENT_PORT,
            "version": Config.DEPLOYMENT_CLIENT_VERSION,
            "status": "SUCCESS",
            "message": "Rollout successfully executed.",
        }
        return response, 201
    except Exception as e:
        payload = {
            "hostname": Config.DEPLOYMENT_CLIENT_HOSTNAME,
            "state": "ERROR",
        }
        http = get_http()
        http.patch(f"{Config.DEPLOYMENT_API_URI}/server", json=payload)

        yum_transaction_id = get_yum_transaction_id()
        yum_rollback_id = yum_transaction_id - 1
        payload = {
            "deployment_id": int(data["deployment_id"]),
            "action": "Update",
            "state": "FAILED",
            "yum_transaction_id": yum_transaction_id,
            "yum_rollback_id": yum_rollback_id,
        }
        http = get_http()
        http.post(
            f"{Config.DEPLOYMENT_API_URI}/server/history/{Config.DEPLOYMENT_CLIENT_HOSTNAME}",
            headers=headers,
            json=payload,
        )

        response = {
            "protocol": Config.DEPLOYMENT_CLIENT_PROTOCOL,
            "hostname": Config.DEPLOYMENT_CLIENT_HOSTNAME,
            "port": Config.DEPLOYMENT_CLIENT_PORT,
            "version": Config.DEPLOYMENT_CLIENT_VERSION,
            "status": "FAILED",
            "message": "POST rollout failed.",
            "exception": str(e),
        }
        return response, 409
