import os
from dotenv import load_dotenv
from collections import OrderedDict


class LastUpdated(OrderedDict):
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)


if os.getenv("ENV_FILE"):
    load_dotenv(os.getenv("ENV_FILE"))
elif os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("/etc/default/dclient"):
    load_dotenv("/etc/default/dclient")
else:
    raise Exception("No Environment File Found!")


def get_config():
    if os.getenv("CONFIG_FILE"):
        config_file = os.getenv("CONFIG_FILE")
    else:
        config_file = "/etc/deployment/dclient.conf"

    if os.path.exists(config_file):
        config = LastUpdated()
        with open(config_file) as cfg:
            for line in cfg:
                try:
                    (k, v) = line.split("=", 1)
                    v = v.rstrip("\n")
                    config[k] = v
                except Exception:
                    pass
        return config
    else:
        return None


def get_var(var):
    config = get_config()
    if os.getenv(var):
        return os.getenv(var)
    else:
        if config:
            if var in config:
                return config[var]
            else:
                return None
        else:
            return None


class Config(object):
    SERVER_ID = get_var("SERVER_ID")
    DEPLOYMENT_CLIENT_PROTOCOL = get_var("DEPLOYMENT_CLIENT_PROTOCOL")
    DEPLOYMENT_CLIENT_HOSTNAME = get_var("DEPLOYMENT_CLIENT_HOSTNAME")
    DEPLOYMENT_CLIENT_PORT = get_var("DEPLOYMENT_CLIENT_PORT")
    DEPLOYMENT_CLIENT_VERSION = get_var("DEPLOYMENT_CLIENT_VERSION")
    DEPLOYMENT_CLIENT_IP = get_var("DEPLOYMENT_CLIENT_IP")

    STATE = get_var("STATE")
    TESTING = bool(int(get_var("TESTING")))

    LOCATION = get_var("LOCATION")
    ENVIRONMENT = get_var("ENVIRONMENT")
    GROUP = get_var("GROUP")

    DEPLOYMENT_PROXY_PROTOCOL = get_var("DEPLOYMENT_PROXY_PROTOCOL")
    DEPLOYMENT_PROXY_HOSTNAME = get_var("DEPLOYMENT_PROXY_HOSTNAME")
    DEPLOYMENT_PROXY_PORT = get_var("DEPLOYMENT_PROXY_PORT")
    DEPLOYMENT_PROXY_VERSION = get_var("DEPLOYMENT_PROXY_VERSION")
    DEPLOYMENT_API_URI = (
        f"{DEPLOYMENT_PROXY_PROTOCOL}://{DEPLOYMENT_PROXY_HOSTNAME}:"
        f"{DEPLOYMENT_PROXY_PORT}/api/{DEPLOYMENT_PROXY_VERSION}"
    )
    TOKEN = get_var("TOKEN")
    ENV_FILE = get_var("ENV_FILE")
    RETRY = get_var("RETRY")
    BACKOFF_FACTOR = get_var("BACKOFF_FACTOR")
    STATUS_FORCELIST = get_var("STATUS_FORCELIST")
    METHOD_WHITELIST = get_var("METHOD_WHITELIST")
    DEFAULT_TIMEOUT = get_var("DEFAULT_TIMEOUT")
    LOG_LEVEL = get_var("LOG_LEVEL")
    LOG_FILE = get_var("LOG_FILE")
    LOG_MAX_BYTES = get_var("LOG_MAX_BYTES")
    LOG_BACKUP_COUNT = get_var("LOG_BACKUP_COUNT")
