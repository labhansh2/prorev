from notify_run import Notify
import time
import logging

logger = logging.getLogger(__name__)


class Notifications(Notify):

    def __init__(self, endpoint=None):
        super().__init__(endpoint)
        if endpoint:
            self.endpoint = endpoint

    def get_endpoint(self, mode='link'):
        logger.info('Notification Endpoint Registration')
        epi = self.register()
        if mode == 'all':
            return epi
        elif mode == 'link':
            return epi.endpoint, epi.channel_page

    def send_notification(self, task_obj: dict):
        logger.info(
            f"Sending Notification: {task_obj['task']}: Round {task_obj['round_no']}")
        self.send(message=f"{task_obj['task']}\nRound {task_obj['round_no']}")


if __name__ == "__main__":
    """test"""
    notif = Notifications()
    ep, cp = notif.get_endpoint()
    print(ep)
    print(cp)
    time.sleep(20)

    notify = Notifications(endpoint=ep)
    notify.send_notification({
        "task": "[test 101] if you get this notification text me",
        "round_no": 1
    })
