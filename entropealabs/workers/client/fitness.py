import httplib2
import entropealabs.util.nanoseconds
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from googleapiclient.errors import HttpError


class Fitness(object):

    def __init__(self, client, dataset):
        self.client = client
        self.google = self.get_google_client(client.google_token)
        self.data_set = dataset
        self.run()

    def get_google_client(self, token):
        credentials = OAuth2Credentials.from_json(token)
        http = credentials.authorize(httplib2.Http())
        google = build('fitness', 'v1', http=http)
        return google

    def run(client):
        res = client.users().dataSources().datasets().get(
            userId='me',
            dataSourceId='derived:com.google.step_count.delta:com.google.android.gms:estimated_steps',
            datasetId=self.dataset
        ).execute()
        logging.info("Last: {}".format(self.dataset)
        logging.info("Data Points: {}".format(len(res.get('point', []))))
