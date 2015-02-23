from capuchin.app import Capuchin
from capuchin import config
from capuchin import db
from flask_oauth import OAuth
import urlparse
import logging
import time
import requests
import datetime
from slugify import slugify
from pprint import pprint

date_format = "%Y-%m-%dT%H:%M:%S+0000"

class Insights():

    def __init__(self, client, id, since, typ=None):
        self.oauth = OAuth()
        self.id = id
        self.type = typ
        self.client = client
        self.since = since
        self.INFLUX = db.init_influxdb()
        self.fb_app = self.oauth.remote_app(
            'facebook',
            base_url='https://graph.facebook.com/',
            request_token_url=None,
            access_token_url='/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            consumer_key=config.FACEBOOK_APP_ID,
            consumer_secret=config.FACEBOOK_APP_SECRET,
        )
        self.fb_app.tokengetter(self.get_token)
        self.get_insights()

    def get_token(self):
        return (self.client.facebook_page.token, config.FACEBOOK_APP_SECRET)

    def write_data(self, data):
        for insight in data.get("data", []):
            if insight.get("period") not in ["day", "lifetime"]: continue
            period = insight.get("period")
            url = "{}.{}".format(insight.get("name"), period)
            if self.type:
                url = "{}.{}.{}".format(self.type, self.id, url)

            points = []
            for event in insight.get("values"):
                if event.get("end_time"):
                    tm = time.mktime(time.strptime(event.get("end_time"), date_format))
                else:
                    tm = time.time()
                val = event.get("value")
                if val == []: continue
                if isinstance(val, dict):
                    for k,v in val.iteritems():
                        t = slugify(k)
                        points.append((tm, v, t))
                else:
                    points.append((tm, val, insight.get("name")))
            if points:
                self.write_influx(points, url)

    def get_insights(self):
        id = self.id
        data = {}
        data['since'] = time.mktime(self.since.timetuple())
        data['until'] = time.mktime(datetime.datetime.utcnow().timetuple())
        res = self.fb_app.get(
            "/v2.2/{}/insights".format(id),
            data=data,
        )
        self.write_data(res.data)
        self.page(res.data)

    def page(self, data):
        nex = data.get("paging", {}).get("next")
        last = nex
        while nex:
            res = requests.get(nex)
            data = res.json()
            self.write_data(data)
            nex = data.get("paging", {}).get("nex")

        return True

    def write_influx(self, points, url):
        data = [
            dict(
                name = "insights.{}.{}".format(self.client._id, url),
                columns = ["time", "value", "type"],
                points = points
            )
        ]
        logging.info("Writing: {}".format(data))
        try:
            res = self.INFLUX.write_points(data)
            logging.info(res)
        except Exception as e:
            logging.warning(e)
