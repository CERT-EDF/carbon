"""Carbon API module"""

from aiohttp.web import Application, get, post, put
from edf_fusion.helper.logging import get_logger

from .case import (
    api_case_categories_get,
    api_case_restore_tl_event_put,
    api_case_star_tl_event_put,
    api_case_subscribe_get,
    api_case_tl_event_get,
    api_case_tl_event_post,
    api_case_tl_event_put,
    api_case_tl_events_export,
    api_case_tl_events_get,
    api_case_trash_get,
    api_case_trash_tl_event_put,
    api_case_users_get,
    api_cases_stats_get,
    attach_case_impl,
    create_case_impl,
    enumerate_cases_impl,
    retrieve_case_impl,
    update_case_impl,
)

_LOGGER = get_logger('server.api', root='carbon')


def setup_api(webapp: Application):
    """Setup webapp routes"""
    _LOGGER.info("install carbon api...")
    webapp.add_routes(
        [
            get('/api/case/{case_guid}/categories', api_case_categories_get),
            get('/api/case/{case_guid}/subscribe', api_case_subscribe_get),
            get('/api/case/{case_guid}/users', api_case_users_get),
            get('/api/case/{case_guid}/trash', api_case_trash_get),
            get('/api/case/{case_guid}/events', api_case_tl_events_get),
            get(
                '/api/case/{case_guid}/events/export',
                api_case_tl_events_export,
            ),
            post('/api/case/{case_guid}/event', api_case_tl_event_post),
            get(
                '/api/case/{case_guid}/event/{tl_event_guid}',
                api_case_tl_event_get,
            ),
            put(
                '/api/case/{case_guid}/event/{tl_event_guid}',
                api_case_tl_event_put,
            ),
            put(
                '/api/case/{case_guid}/event/{tl_event_guid}/restore',
                api_case_restore_tl_event_put,
            ),
            put(
                '/api/case/{case_guid}/event/{tl_event_guid}/star',
                api_case_star_tl_event_put,
            ),
            put(
                '/api/case/{case_guid}/event/{tl_event_guid}/trash',
                api_case_trash_tl_event_put,
            ),
            get('/api/cases/stats', api_cases_stats_get),
        ]
    )
    _LOGGER.info("carbon api installed.")
