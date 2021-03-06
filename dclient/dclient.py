#!/usr/bin/python3
from dclient.util.config import Config
from dclient.controllers.rollout import post_rollout
from dclient.controllers.rollback import post_rollback
from dclient.util.core import set_state, register_dclient
from dclient.controllers.healthcheck import get_healthcheck
from dclient.controllers.versionlock import get_versionlock

from flask import Flask, request
from gunicorn.app.wsgiapp import WSGIApplication

import logging.handlers

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
)

rotating_log_handeler = logging.handlers.RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=int(Config.LOG_MAX_BYTES),
    backupCount=int(Config.LOG_BACKUP_COUNT),
)
rotating_log_handeler.setFormatter(formatter)
rotating_log_handeler.setLevel(logging.DEBUG)
logging.getLogger("gunicorn.error").addHandler(rotating_log_handeler)


class DClient(WSGIApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(WSGIApplication, self).__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def create_app():
    """Create the dclient app

    :return: app
    """

    app = Flask(__name__)
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.config.from_object(Config)

    with app.app_context():
        if not Config.TESTING:
            if not Config.TOKEN:
                register_dclient()
            else:
                set_state("ACTIVE")

        @app.route("/", methods=["GET"])
        def healthcheck():
            if request.method == "GET":
                return get_healthcheck()

        @app.route("/rollout", methods=["POST"])
        def rollout():
            if request.method == "POST":
                return post_rollout()

        @app.route("/rollback", methods=["POST"])
        def rollback():
            if request.method == "POST":
                return post_rollback()

        @app.route("/versionlock", methods=["GET", "POST"])
        def versionlock():
            if request.method == "GET":
                return get_versionlock()

    return app


if __name__ == "__main__":
    options = {
        "bind": "%s:%s" % ("0.0.0.0", "8003"),
        "workers": 1,
        "reload-engine": "auto",
        "spew": False,
        "access-logformat": "%(h)s %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s'",
        "disable-redirect-access-to-syslog": False,
        "log-level": "debug",
        "capture-output": True,
        "worker_class": "sync",
        "timeout": 600,
    }
    DClient(create_app(), options).run()
