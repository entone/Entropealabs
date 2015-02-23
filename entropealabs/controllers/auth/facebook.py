from flask import Blueprint, render_template, request, redirect, url_for, Response
from flask.views import MethodView
from flask.ext.login import login_required, current_user
from entropealabs import config
from entropealabs.models.client import Client, SocialAccount, FacebookPage, PageCategory
from flask_oauth import OAuth
import logging
from urlparse import parse_qs, urlparse
import json

oauth = OAuth()

facebook = Blueprint(
    "facebook",
    __name__,
    template_folder=config.TEMPLATES,
    subdomain=config.ADMIN_SUBDOMAIN,
    url_prefix="/auth/facebook",
)

fb_app = oauth.remote_app(
    'facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key="841699302554888",
    consumer_secret="415f6cd36c605c47486dedcf27dbe23a",
    request_token_params={'scope': 'manage_pages,read_insights,ads_management'}
)

@fb_app.tokengetter
def get_facebook_token(token=None):
    sa = current_user.social.facebook
    return (sa.token, sa.secret)

@facebook.route("/login", methods=['GET', 'POST'])
@login_required
def login():
    return fb_app.authorize(
        callback=url_for('.authorized',
            next=request.args.get('next'), _external=True)
    )

@facebook.route("/authorized", methods=['GET', 'POST'])
@fb_app.authorized_handler
@login_required
def authorized(resp):
    if resp is None:
        flash("You denied the request", "danger")
        return redirect(url_for(".index"))

    try:
        sa = current_user.social.facebook
        sa.token = resp.get('access_token')
        current_user.save()
    except Exception as e:
        logging.exception(e)

    return redirect(url_for(".verify"))

def get_pages(user_id):
    pages = []
    res = fb_app.get("/{}/accounts".format(user_id))
    pages = [p for p in res.data.get("data")]
    while res.data.get("paging", {}).get("next"):
        res = fb_app.get(
            "/{}/accounts".format(user_id),
            data={
                "after":res.data.get("paging", {}).get("cursor").get("after")
            }
        )
        pages+= [p for p in res.data.get("data")]

    return pages

def get_long_token(token):
    fb = current_user.social.facebook
    logging.info(fb._json())
    long_token = fb_app.get(
        "/oauth/access_token",
        data={
            'grant_type':'fb_exchange_token',
            'fb_exchange_token':token,
            'client_id':fb.app_id,
            'client_secret':fb.secret,
        }
    )
    token = parse_qs(long_token.data, keep_blank_values=True)
    return {'token':token.get('access_token', [""])[0], 'expires':token.get('expires', [""])[0]}

class Index(MethodView):
    decorators = [ login_required, ]

    def get(self):
        fb = current_user.social.facebook
        if fb.app_id and not fb.token:
            return redirect(url_for('.login'))
        elif not fb.app_id:
            fields = [
                ["app_id","ID"],
                ["secret", "Secret"],
            ]
            return render_template("auth/social_account.html", type="Facebook", fields=fields)
        elif current_user.facebook_pages:
            return render_template("auth/facebook/view_pages.html")

class Configure(MethodView):
    decorators = [ login_required, ]
    def post(self):
        logging.info(request.form)
        current_user.social.facebook(data={
            "app_id":request.form.get("app_id"),
            "secret":request.form.get("secret"),
        })
        current_user.save()
        return redirect(url_for('.index'))


class Verify(MethodView):
    decorators = [ login_required, ]
    def get(self):
        return render_template("auth/facebook/load_pages.html")

class LoadPages(MethodView):
    decorators = [ login_required, ]
    def get(self):
        sa = current_user.social.facebook
        res = fb_app.get(
            "/debug_token",
            data={
                'input_token':sa.token
            }
        )
        if res:
            data = res.data.get('data')
            sa.id = data.get("user_id")
            sa.app_id = data.get("app_id")
            [sa.permissions.append(p) for p in data.get("scopes") if p not in sa.permissions]
            current_user.save()
            token = get_long_token(sa.token)
            sa.token = token['token']
            sa.expires = token['expires']
            current_user.save()
            pages = get_pages(sa.id)
            logging.info(pages)
            for page in pages:
                for p in current_user.facebook_pages:
                    if page.get("id") == p.id:
                        break
                else:
                    fp = FacebookPage()
                    fp.name = page.get("name")
                    fp.token = page.get("access_token")
                    fp.id = page.get("id")
                    [fp.permissions.append(perm) for perm in page.get("perms")]
                    for pc in page.get("category_list", []):
                        pca = PageCategory()
                        pca.id = pc.get("id")
                        pca.name = pc.get("name")
                        fp.categories.append(pca)
                    current_user.facebook_pages.append(fp)
            current_user.save()
        return render_template("auth/facebook/pages.html")

class SavePage(MethodView):
    decorators = [login_required,]

    def post(self):
        id = request.form["id"]
        logging.info(id);
        for p in current_user.facebook_pages:
            if p.id == id:
                client = Client(id=current_user.client._id)
                fb = client.social.facebook
                fb.id = p.id
                fb.app_id = current_user.social.facebook.app_id
                fb.name=p.name
                fb.token = p.token
                fb.secret = current_user.social.facebook.secret
                fb.permissions = p.permissions
                fb.categories = p.categories
                client.save()
                break

        return Response(json.dumps({'id':id}), mimetype='application/json')

facebook.add_url_rule("/", view_func=Index.as_view('index'))
facebook.add_url_rule("/verify", view_func=Verify.as_view('verify'))
facebook.add_url_rule("/loadpages", view_func=LoadPages.as_view('load_pages'))
facebook.add_url_rule("/save_page", view_func=SavePage.as_view('save_page'))
facebook.add_url_rule("/configure", view_func=Configure.as_view('configure'))
