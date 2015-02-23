from capuchin.app import Capuchin
from capuchin import config
from capuchin import db
from capuchin.insights import POST_INSIGHTS
from capuchin.workers.client.insights import Insights
from flask_oauth import OAuth
import urlparse
import logging
import time
import requests
import datetime
from pprint import pprint
from slugify import slugify

date_format = "%Y-%m-%dT%H:%M:%S+0000"

class ClientPosts():

    def __init__(self, client, since):
        self.oauth = OAuth()
        self.client = client
        self.since = since
        self.INFLUX = db.init_influxdb()
        self.ES = db.init_elasticsearch()
        self.fb_app = self.oauth.remote_app(
            'facebook',
            base_url='https://graph.facebook.com',
            request_token_url=None,
            access_token_url='/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            consumer_key=config.FACEBOOK_APP_ID,
            consumer_secret=config.FACEBOOK_APP_SECRET,
        )
        self.fb_app.tokengetter(self.get_token)
        self.get_feed()

    def get_token(self):
        return (self.client.facebook_page.token, config.FACEBOOK_APP_SECRET)

    def get_count(self, url):
        name = "insights.{}.post.{}".format(self.client._id, url)
        q = "select count(type) from {}".format(name)
        try:
            res = self.INFLUX.query(q)
            return res[0]['points'][0][1]
        except Exception as e:
            logging.warn(e)
            return None


    def write_data(self, post):
        p_id = post.get("id")
        post['client'] = str(self.client._id)
        self.ES.index(
            index=config.ES_INDEX,
            doc_type=config.POST_RECORD_TYPE,
            body=post,
            id=p_id
        )
        shares = post.get("shares", {}).get("count", 0)
        tm = time.time()
        self.write_influx([(tm, shares, 'shares')], url="{}.{}".format(p_id, "shares"))
        for i in POST_INSIGHTS:
            url = "{}.{}".format(p_id, i)
            count = self.get_count(url)
            points = [(time.time(), 0, i)] if count == None else []
            data = post.get(i)
            for d in data[count:]:
                ct = d.get("created_time")
                if ct:
                    tm = time.mktime(time.strptime(d.get("created_time"), date_format))
                    logging.info("Comment Time:{}".format(tm))
                else:
                    tm = time.time()

                points.append((tm, 1, i))

            self.write_influx(points, url)

    def get_feed(self):
        id = self.client.facebook_page.id
        data = {"limit":250}
        if self.since:
            data['since'] = time.mktime(self.since.timetuple())
        res = self.fb_app.get(
            "/v2.2/{}/feed".format(id),
            data=data,
        )
        for p in res.data.get('data'):
            p_id = p.get("id")
            for i in POST_INSIGHTS:
                p[i] = self.page(p_id, i, p.get(i, {}))
            self.write_data(p)
            since = datetime.datetime.strptime(p.get("created_time"), date_format)
            i = Insights(client=self.client, id=p.get('id'), since=since, typ="post")

    def page(self, post_id, typ, data):
        res = [a for a in data.get("data", [])]
        cursors = data.get("paging", {}).get("cursors", {})
        if cursors.get('before') == cursors.get('after'): return res
        last = {'before':cursors['before'], 'after':cursors['after']}
        for i in last:
            while last[i]:
                resp = self.fb_app.get(
                    "/v2.2/{}/{}".format(post_id, typ),
                    data={
                        "limit":250,
                        i:cursors[i]
                    },
                )
                res+=[a for a in resp.data.get("data")]
                af = resp.data.get("paging", {}).get(i)
                last[i] = af if af != last[i] else None

        return res

    def write_influx(self, points, url):
        data = [
            dict(
                name = "insights.{}.post.{}".format(self.client._id, url),
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
