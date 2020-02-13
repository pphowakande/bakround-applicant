__author__ = "natesymer"

from ..queue import QueueNames
from bakround_applicant.services.base import BaseConsumer
import django
import time

class Consumer(BaseConsumer):
    service_name = "ON_DEMAND_VIEW_REFRESHER_SERVICE"
    queue_name = QueueNames.on_demand_view_refresher

    def handle_message(self, body):
        try:
            time.sleep(20)
            with django.db.connection.cursor() as cursor:
                cursor.execute("select pg_advisory_lock(102)")

                try:
                    cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY profile_info_view")
                    cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY recent_scores_view")
                finally:
                    cursor.execute("select pg_advisory_unlock(102)")

        except Exception as e:
            self.logger.exception(e)
