from flask import Blueprint, Response, render_template
from flask.views import MethodView
from entropealabs import config
import logging

dashboard = Blueprint(
    'dashboard',
    __name__,
    subdomain=config.ADMIN_SUBDOMAIN,
    template_folder=config.TEMPLATES,
)

class Index(MethodView):

    def get(self):
        return render_template("index.html")

dashboard.add_url_rule("/", view_func=Index.as_view('index'))
