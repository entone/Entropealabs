from flask import Blueprint, render_template, request, redirect, url_for, Response
from flask.views import MethodView
from flask.ext.login import login_required, current_user
from entropealabs.models.client import Client
from entropealabs import config
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow, argparser
import logging
import json

google = Blueprint(
    "google",
    __name__,
    template_folder=config.TEMPLATES,
    url_prefix="/auth/google",
)


class Index(MethodView):
    decorators = [ login_required, ]

    def get(self):
        google = current_user.client.social.google
        if google.app_id and not google.token:
            flow = OAuth2WebServerFlow(
                google.app_id,
                google.secret,
                config.GOOGLE_SCOPE,
                redirect_uri=url_for('.verify', _external=True),
            )
            uri = flow.step1_get_authorize_url()
            return redirect(uri)
        elif not google.app_id:
            fields = [
                ["app_id","ID"],
                ["secret", "Secret"],
            ]
            return render_template("auth/social_account.html", type="Google", fields=fields)
        else:
            return render_template("auth/google/verified.html")

class Configure(MethodView):
    decorators = [ login_required, ]
    def post(self):
        client = Client(id=current_user.client._id)
        logging.info(request.form)
        client.social.google(data={
            "app_id":request.form.get("app_id"),
            "secret":request.form.get("secret"),
        })
        client.save()
        return redirect(url_for('.index'))

class Verify(MethodView):
    decorators = [ login_required, ]
    def get(self):
        user = current_user._get_current_object()
        client = Client(id=user.client._id)
        google = client.social.google
        flow = OAuth2WebServerFlow(
            google.app_id,
            google.secret,
            config.GOOGLE_SCOPE,
            redirect_uri=url_for('.verify', _external=True),
        )
        credentials = flow.step2_exchange(code=request.args)
        j = json.loads(credentials.to_json())
        google.id="me"
        google.name="me"
        google.token=j
        google.permissions.append(u"{}".format(config.GOOGLE_SCOPE))
        client.save()
        return render_template("auth/google/verified.html")

google.add_url_rule("/", view_func=Index.as_view('index'))
google.add_url_rule("/verify", view_func=Verify.as_view('verify'))
google.add_url_rule("/configure", view_func=Configure.as_view('configure'))
