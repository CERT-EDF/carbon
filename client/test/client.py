#!/usr/bin/env python3
"""Carbon Test Client"""

from argparse import ArgumentParser
from asyncio import run

from edf_carbon_core.concept import Case, Constant, TimelineEvent
from edf_fusion.client import (
    FusionAuthAPIClient,
    FusionCaseAPIClient,
    FusionClient,
    FusionClientConfig,
    FusionConstantAPIClient,
    FusionInfoAPIClient,
    create_session,
)
from edf_fusion.helper.logging import get_logger
from yarl import URL

from edf_carbon_client import CarbonAPIClient

_LOGGER = get_logger('client', root='test')


async def _playbook(fusion_client: FusionClient):
    fusion_info_api_client = FusionInfoAPIClient(fusion_client=fusion_client)
    fusion_case_api_client = FusionCaseAPIClient(
        case_cls=Case, fusion_client=fusion_client
    )
    fusion_constant_api_client = FusionConstantAPIClient(
        constant_cls=Constant, fusion_client=fusion_client
    )
    carbon_api_client = CarbonAPIClient(fusion_client=fusion_client)
    # retrieve server info
    info = await fusion_info_api_client.info()
    _LOGGER.info("retrieved info: %s", info)
    # retrieve server constant
    constant = await fusion_constant_api_client.constant()
    _LOGGER.info("retrieved constant: %s", constant)
    # create case
    case = await fusion_case_api_client.create_case(
        Case(
            tsid=None,
            name='test case',
            description='test description',
            acs={'DFIR'},
        )
    )
    _LOGGER.info("created case: %s", case)
    # update case
    case.report = 'test case report'
    case = await fusion_case_api_client.update_case(case)
    _LOGGER.info("updated case: %s", case)
    # retrieve case
    case = await fusion_case_api_client.retrieve_case(case.guid)
    _LOGGER.info("retrieved case: %s", case)
    # enumerate cases
    cases = await fusion_case_api_client.enumerate_cases()
    _LOGGER.info("enumerated cases: %s", cases)
    # retrieve users
    users = await carbon_api_client.retrieve_case_users(case.guid)
    _LOGGER.info("retrieved case users: %s", users)
    user = users[0]
    # retrieve categories
    categories = await carbon_api_client.retrieve_case_categories(case.guid)
    _LOGGER.info("retrieved case categories: %s", categories)
    category = categories[0]
    # create timeline event
    tl_event = TimelineEvent(
        title='title_placeholder',
        creator=user.username,
        category=category.name,
        description='description_placeholder',
    )
    tl_event = await carbon_api_client.create_case_tl_event(
        case.guid, tl_event
    )
    _LOGGER.info("created case timeline event: %s", tl_event)
    # update timeline event
    tl_event.title = 'updated_title_placeholder'
    tl_event = await carbon_api_client.update_case_tl_event(
        case.guid, tl_event
    )
    _LOGGER.info("updated case timeline event: %s", tl_event)
    # trash timeline event
    tl_event = await carbon_api_client.trash_case_tl_event(
        case.guid, tl_event.guid
    )
    _LOGGER.info("trashed case timeline event: %s", tl_event)
    # retrieve trashed timeline events
    tl_events = await carbon_api_client.retrieve_case_trashed_tl_events(
        case.guid
    )
    _LOGGER.info("trashed case timeline events: %s", tl_events)
    # retrieve timeline events
    tl_events = await carbon_api_client.retrieve_case_tl_events(case.guid)
    _LOGGER.info("case timeline events: %s", tl_events)
    # restore timeline event
    tl_event = await carbon_api_client.restore_case_tl_event(
        case.guid, tl_event.guid
    )
    _LOGGER.info("restored case timeline event: %s", tl_event)
    # retrieve timeline event
    tl_event = await carbon_api_client.retrieve_case_tl_event(
        case.guid, tl_event.guid
    )
    _LOGGER.info("retrieved case timeline event: %s", tl_event)
    # retrieve timeline events
    tl_events = await carbon_api_client.retrieve_case_tl_events(case.guid)
    _LOGGER.info("case timeline events: %s", tl_events)
    # retrieve trashed timeline events
    tl_events = await carbon_api_client.retrieve_case_trashed_tl_events(
        case.guid
    )
    _LOGGER.info("trashed case timeline events: %s", tl_events)
    # retrieve all users
    users = await carbon_api_client.retrieve_users()
    _LOGGER.info("retrieved users: %s", users)


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--port', '-p', type=int, default=10000, help="Server port"
    )
    return parser.parse_args()


async def app():
    """Application entrypoint"""
    args = _parse_args()
    config = FusionClientConfig(api_url=URL(f'http://127.0.0.1:{args.port}/'))
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
            await _playbook(fusion_client)
        finally:
            await fusion_auth_api_client.logout()


if __name__ == '__main__':
    run(app())
