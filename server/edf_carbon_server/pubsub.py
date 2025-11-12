"""Carbon PubSub"""

from uuid import UUID

from aiohttp.web import Application, Request
from edf_carbon_core.concept import Notification
from edf_fusion.helper.aiohttp import pubsub_sse_response
from edf_fusion.helper.pubsub import PubSub
from edf_fusion.helper.redis import get_redis

_CARBON_PUBSUB = 'carbon_pubsub'


def setup_pubsub(webapp: Application):
    """Setup pub/sub instance"""
    redis = get_redis(webapp)
    webapp[_CARBON_PUBSUB] = PubSub(redis=redis)


async def publish(request: Request, notification: Notification):
    """Publish"""
    pubsub = request.app[_CARBON_PUBSUB]
    channel = f'carbon-pubsub-case-{notification.case_guid}'
    await pubsub.publish(notification, channel)


async def subscribe(request: Request, client_guid: str, case_guid: UUID):
    """Subscribe"""
    pubsub = request.app[_CARBON_PUBSUB]
    channel = f'carbon-pubsub-case-{case_guid}'
    response = await pubsub_sse_response(request, pubsub, client_guid, channel)
    return response


async def subscribers(request: Request, case_guid: UUID) -> set[str]:
    """Retrieve case subscribers"""
    pubsub = request.app[_CARBON_PUBSUB]
    return pubsub.subscribers(case_guid)
