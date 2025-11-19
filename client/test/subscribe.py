#!/usr/bin/env python3
"""Carbon Test Client"""

from argparse import ArgumentParser
from asyncio import gather, run
from uuid import UUID

from edf_carbon_core.concept import Case
from edf_fusion.client import (
    FusionAuthAPIClient,
    FusionCaseAPIClient,
    FusionClient,
    FusionClientConfig,
    FusionEventAPIClient,
    create_session,
)
from edf_fusion.helper.logging import get_logger
from yarl import URL

from edf_carbon_client import CarbonClient

_LOGGER = get_logger('subscribe', root='test')


async def _fusion_subscriber(fusion_client: FusionClient, case: Case):
    fusion_event_api_client = FusionEventAPIClient(fusion_client=fusion_client)
    async for event in fusion_event_api_client.subscribe(case.guid):
        _LOGGER.info("%s", event)


async def _carbon_subscriber(fusion_client: FusionClient, case: Case):
    carbon_client = CarbonClient(fusion_client=fusion_client)
    async for notification in carbon_client.subscribe(case.guid):
        _LOGGER.info("%s", notification)


async def _playbook(fusion_client: FusionClient, case_guid: UUID):
    fusion_case_api_client = FusionCaseAPIClient(
        case_cls=Case, fusion_client=fusion_client
    )
    case = await fusion_case_api_client.retrieve_case(case_guid)
    await gather(
        _fusion_subscriber(fusion_client, case),
        _carbon_subscriber(fusion_client, case),
    )


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--api-url',
        type=URL,
        default=URL('http://carbon.domain.lan/'),
        help="API URL",
    )
    parser.add_argument('case_guid', type=UUID, help="Case GUID")
    return parser.parse_args()


async def app():
    """Application entrypoint"""
    args = _parse_args()
    config = FusionClientConfig(api_url=args.api_url)
    session = create_session(config, unsafe=True)
    async with session:
        fusion_client = FusionClient(config=config, session=session)
        fusion_auth_api_client = FusionAuthAPIClient(
            fusion_client=fusion_client
        )
        identity = await fusion_auth_api_client.login('test', 'test')
        if not identity:
            return
        _LOGGER.info("logged as: %s", identity)
        try:
            await _playbook(fusion_client, args.case_guid)
        finally:
            await fusion_auth_api_client.logout()


if __name__ == '__main__':
    run(app())
