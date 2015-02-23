from werkzeug.wsgi import peek_path_info
from entropealabs import config
from gevent import monkey
import logging

monkey.patch_all()

def create_app():
    logging.basicConfig(level=config.LOG_LEVEL)
    logging.info("Initializing")
    def app(env, start_response):
        from entropealabs import config
        from entropealabs.app import App
        _app = App()
        if peek_path_info(env) == "healthcheck":
            _app.config['SERVER_NAME'] = None
        else:
            _app.config['SERVER_NAME'] = config.SERVER_NAME

        return _app(env, start_response)

    logging.info("Running")
    return app

app = create_app()
