from flask import Blueprint, Response, render_template
from flask.views import MethodView
from entropealabs import config
import logging

homepage = Blueprint(
    'homepage',
    __name__,
    template_folder=config.TEMPLATES,
)

class Index(MethodView):

    def get(self):
        return render_template("homepage.html")

homepage.add_url_rule("/", view_func=Index.as_view('index'))
