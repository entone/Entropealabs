from flask import Flask
from flask.ext.script import Manager
from flask.ext.script import Command, Option

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run_flow, argparser

from entropealabs.app import App
from entropealabs import config
from entropealabs.models.client import Client
import sys
import logging

app = App()
manager = Manager(app)

class AuthGoogle(Command):

    def run(self):
        flow = OAuth2WebServerFlow(
            config.GOOGLE_CLIENT_ID,
            config.GOOGLE_CLIENT_SECRET,
            config.GOOGLE_SCOPE
        )
        storage = Storage('google.json')
        flags = argparser.parse_args(['--noauth_local_webserver'])
        run_flow(flow, storage, flags)

class InitApp(Command):

    def  run(self):
        es = db.init_elasticsearch()
        db.create_index(es)
        influx = db.init_influxdb()
        db.create_shards(influx)

class CopyGoogleJWT(Command):

    option_list = (
        Option('--client_id', '-cid', dest='client_id')
    )

    def run(self, client_id):
        client = Client(id=id)
        with open("google.json") as jwt:
            d = json.loads(jwt.read())
            client.google_token = d
            client.save()

manager.add_command('init', InitApp())
manager.add_command('auth_google', AuthGoogle())
manager.add_command('save_google', CopyGoogleJWT())

if __name__ == "__main__":
    manager.run()
