from dclient.util.logger import get_logger
from dclient.util.config import Config, get_var
from dclient.util.http_helper import get_http

import os
import re
from dotenv import load_dotenv
from collections import OrderedDict
from subprocess import Popen, check_output

load_dotenv("/etc/default/dclient")
logger = get_logger()


class LastUpdated(OrderedDict):

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)


def get_installed(rpm):
    logger.info(f"running check_output(['rpm', '-q', {rpm}])")
    package = check_output(["rpm", "-q", rpm])
    z = re.match("not installed", package)
    if z:
        return False
    else:
        return True


def get_yum_transaction_id():
    logger.info("running check_output(['sudo', 'yum', 'history', 'list''])")
    history_list = check_output(["sudo", "yum", "history", "list"])
    history_list = history_list.splitlines()
    count = 0
    fl = 0
    for line in history_list:
        line = str(line, 'utf-8')
        z = re.match("^-+$", line)
        if z:
            fl = count + 1
            count += 1
        else:
            count += 1
    first = history_list[fl]
    first = str(first, 'utf-8')
    first = first.split("|")
    tid = first[0]
    tid = int(tid)
    return tid


def install_pkgs(packages):
    packages = ' '.join(map(str, packages))
    logger.info("running os.system('sudo yum clean all')")
    os.system("sudo yum clean all")
    logger.info(f"running sudo yum --enablerepo=Production -y install {packages}")
    stat = os.system(f"sudo yum --enablerepo=Production -y install {packages}")
    if stat != 0:
        raise Exception(stat)


def restart_service(service):
    logger.info(f"running Popen(['sudo', 'systemctl', 'restart', {service}])")
    Popen(["sudo", "systemctl", "restart", service])


def update_env(key, value):
    """
    Update environment variables and store environment file
    :param key:
    :param value:
    :return:
    """
    env = LastUpdated()
    with open("/etc/default/dclient") as f:
        for line in f:
            (k, v) = line.split("=", 1)
            env[k] = v
    env[key] = value
    os.environ[key] = value

    with open("/etc/default/dclient", "w") as f:
        for k in env.keys():
            line = f"{k}={env[k]}"
            if "\n" in line:
                f.write(line)
            else:
                f.write(line+"\n")


def set_state(state):
    """
    Set the dclient state to the correct state.
    Keep the state in sync with Deployment-api
    :return:
    """
    data = {"hostname": get_var("HOSTNAME"), "state": state}
    http = get_http()
    r = http.patch(f"{Config.DEPLOYMENT_API_URI}/server", json=data)
    if r.status_code == 201:
        logger.debug(f"Successfully Updated State: {state}")
        return True
    else:
        logger.error(f"Failed to set state: {state}")
        return False


def register_dclient():
    """
    Register dclient and fetch token
    :return:
    """
    data = {
        "created_by": "dclient",
        "hostname": get_var("HOSTNAME"),
        "ip": get_var("IP"),
        "state": "ACTIVE",
        "group": get_var("GROUP"),
        "environment": get_var("ENVIRONMENT"),
        "location": get_var("LOCATION"),
        "url": get_var("URL"),
        "deployment_proxy": get_var("DEPLOYMENT_PROXY")
    }
    http = get_http()
    r = http.post(f"{Config.DEPLOYMENT_API_URI}/register", json=data)
    resp = r.json()
    logger.debug(f"REGISTER CLIENT: {resp}")
    if "token" in resp:
        update_env("TOKEN", resp["token"])
        set_state("ACTIVE")
        return True
    else:
        set_state("ERROR")
        return False