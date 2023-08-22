import os

import pusher


class PusherSocket:
    app_id = os.environ.get("PUSHER_APP_ID")
    key = os.environ.get("PUSHER_KEY")
    secret = os.environ.get("PUSHER_SECRET")
    cluster = os.environ.get("PUSHER_CLUSTER")

    def __init__(self):
        self.pusher_client = pusher.Pusher(
            app_id=self.app_id,
            key=self.key,
            secret=self.secret,
            ssl=True,
            cluster=self.cluster,
        )

    def trigger(self, channel, event, data):
        print("===================================================")
        print("PUSHER DATA: ", data)
        print("===================================================")
        self.pusher_client.trigger(channel, event, data)
