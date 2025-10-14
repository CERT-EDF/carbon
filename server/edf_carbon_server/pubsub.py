"""Carbon PubSub"""

from uuid import UUID

from aiohttp.web import Application, Request
from edf_carbon_core.concept import Notification
from edf_fusion.helper.aiohttp import pubsub_sse_response
from edf_fusion.helper.pubsub import PubSub

_CARBON_PUBSUB = 'carbon_pubsub'


def setup_pubsub(webapp: Application):
    """Setup pub/sub instance"""
    webapp[_CARBON_PUBSUB] = PubSub()


async def publish(request: Request, notification: Notification):
    """Publish"""
    pubsub = request.app[_CARBON_PUBSUB]
    await pubsub.publish(notification, str(notification.case_guid))


async def subscribe(request: Request, client_guid: str, case_guid: UUID):
    """Subscribe"""
    pubsub = request.app[_CARBON_PUBSUB]
    response = await pubsub_sse_response(
        request, pubsub, client_guid, str(case_guid)
    )
    return response


async def subscribers(request: Request, case_guid: UUID) -> set[str]:
    """Retrieve case subscribers"""
    pubsub = request.app[_CARBON_PUBSUB]
    usernames = await pubsub.subscribers(case_guid)
    return set(usernames)
