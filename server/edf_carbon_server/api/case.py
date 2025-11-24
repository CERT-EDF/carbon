"""/api/case* routes implementation"""

from uuid import UUID

from aiohttp.web import Request
from edf_carbon_core.concept import TASK_CATEGORY, Case
from edf_fusion.helper.aiohttp import (
    get_guid,
    get_json_body,
    json_response,
    stream_response,
)
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.streaming import stream_from_text
from edf_fusion.server.case import (
    AttachContext,
    CreateContext,
    DeleteContext,
    EnumerateContext,
    RetrieveContext,
    UpdateContext,
)
from edf_fusion.server.constant import get_fusion_const_api
from edf_fusion.server.event import get_fusion_evt_api
from edf_fusion.server.storage import get_fusion_storage

from .helper import prologue

_LOGGER = get_logger('server.api.case', root='carbon')


def _get_guid(request: Request, element: str) -> UUID | None:
    try:
        return UUID(request.match_info[element])
    except ValueError:
        return None


async def _is_pending(storage, case_guid: str, tl_event_guid: str) -> bool:
    return tl_event_guid not in [
        tl_event
        async for tl_event in storage.retrieve_closed_tl_events(case_guid)
    ]


async def attach_case_impl(ctx: AttachContext) -> Case | None:
    """Attach case"""
    storage = get_fusion_storage(ctx.request)
    success = await storage.attach_case(ctx.case_guid, ctx.next_case_guid)
    if not success:
        return None
    case = await storage.retrieve_case(ctx.next_case_guid)
    return case


async def create_case_impl(ctx: CreateContext) -> Case | None:
    """Create case"""
    storage = get_fusion_storage(ctx.request)
    case = await storage.create_case(ctx.managed, ctx.body)
    if not case:
        return None
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    await fusion_evt_api.notify(
        category='create_case', case=case, ext={'user': ctx.identity.username}
    )
    return case


async def update_case_impl(ctx: UpdateContext) -> Case | None:
    """Update case"""
    storage = get_fusion_storage(ctx.request)
    case = await storage.update_case(ctx.case_guid, ctx.body)
    if not case:
        return None
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    await fusion_evt_api.notify(
        category='update_case', case=case, ext={'user': ctx.identity.username}
    )
    return case


async def delete_case_impl(ctx: DeleteContext) -> bool:
    """Delete case"""
    storage = get_fusion_storage(ctx.request)
    fusion_evt_api = get_fusion_evt_api(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    deleted = await storage.delete_case(ctx.case_guid)
    if deleted:
        await fusion_evt_api.notify(
            category='delete_case',
            case=case,
            ext={'user': ctx.identity.username},
        )
    return deleted


async def retrieve_case_impl(ctx: RetrieveContext) -> Case | None:
    """Retrieve case"""
    storage = get_fusion_storage(ctx.request)
    case = await storage.retrieve_case(ctx.case_guid)
    return case


async def enumerate_cases_impl(ctx: EnumerateContext) -> list[Case]:
    """Enumerate cases"""
    storage = get_fusion_storage(ctx.request)
    return [case async for case in storage.enumerate_cases()]


async def api_case_categories_get(request: Request):
    """Retrieve case applicable categories"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    _, storage = await prologue(
        request, 'case_categories', context={'case_guid': case_guid}
    )
    case = await storage.retrieve_case(case_guid)
    if not case:
        return json_response(status=404, message="Case not found")
    fusion_const_api = get_fusion_const_api(request)
    constant = fusion_const_api.cached_constant
    categories = [
        category
        for category in constant.categories.values()
        if not category.groups or category.groups.intersection(case.acs)
    ]
    return json_response(data=[category.to_dict() for category in categories])


async def api_case_tl_event_get(request: Request):
    """Retrieve case timeline event"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    _, storage = await prologue(
        request,
        'retrieve_event',
        context={'case_guid': case_guid, 'tl_event_guid': tl_event_guid},
    )
    tl_event = await storage.retrieve_tl_event(case_guid, tl_event_guid)
    if not tl_event:
        return json_response(status=404, message="Timeline event not found")
    return json_response(data=tl_event.to_dict())


async def api_case_tl_event_post(request: Request):
    """Create case timeline event"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    identity, storage = await prologue(
        request,
        'create_event',
        context={'case_guid': case_guid, 'case_open_check': True},
    )
    body = await get_json_body(request)
    if not body:
        return json_response(status=400, message="Body is missing")
    body['creator'] = identity.username
    tl_event = await storage.create_tl_event(case_guid, body)
    if not tl_event:
        return json_response(status=400, message="Invalid timeline event")
    data = tl_event.to_dict()
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        category='create_event',
        case=case,
        ext={'user': identity.username, 'data': data},
    )
    return json_response(data=data)


async def api_case_tl_event_put(request: Request):
    """Update case timeline event"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    identity, storage = await prologue(
        request,
        'update_event',
        context={
            'case_guid': case_guid,
            'tl_event_guid': tl_event_guid,
            'case_open_check': True,
        },
    )
    body = await get_json_body(request)
    if not body:
        return json_response(status=400, message="Body is missing")
    tl_event = await storage.update_tl_event(case_guid, tl_event_guid, body)
    if not tl_event:
        return json_response(status=404, message="Timeline event not found")
    data = tl_event.to_dict()
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        category='update_event',
        case=case,
        ext={'user': identity.username, 'data': data},
    )
    return json_response(data=data)


async def api_case_tl_event_delete(request: Request):
    """Delete case timeline event (cannot be restored)"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    identity, storage = await prologue(
        request,
        'delete_event',
        context={
            'case_guid': case_guid,
            'tl_event_guid': tl_event_guid,
            'case_open_check': True,
            'is_delete_op': True,
        },
    )
    deleted = await storage.delete_tl_event(case_guid, tl_event_guid)
    if not deleted:
        return json_response(status=400, message='Not deleted')
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        category='delete_event',
        case=case,
        ext={'user': identity.username, 'event_guid': str(tl_event_guid)},
    )
    return json_response()


async def api_case_tl_events_get(request: Request):
    """Enumerate case timeline events (not trashed)"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    _, storage = await prologue(
        request, 'enumerate_events', context={'case_guid': case_guid}
    )
    return json_response(
        data=[
            tl_event.to_dict()
            async for tl_event in storage.enumerate_tl_events(case_guid)
        ]
    )


async def api_case_tl_events_export(request: Request):
    """Enumerate timeline events to export"""
    case_guid = _get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    _, storage = await prologue(
        request, 'export_events', context={'case_guid': case_guid}
    )
    starred = 'starred' in request.query
    fields = request.query.getall('fields')
    markdown = [
        f"| {' | '.join(fields)} |",
        f"|---{'---|---'.join([''] * len(fields))}---|",
    ]
    async for tl_event in storage.enumerate_tl_events(case_guid):
        if starred and not tl_event.starred:
            continue
        tl_event = tl_event.to_dict()
        cells = [
            tl_event.get(k, 'MISSING KEY').replace('\n', '<br>')
            for k in fields
        ]
        cells = ' | '.join(cells)
        markdown.append(f"| {cells} |")
    response = await stream_response(
        request,
        f'{case_guid}-export.md',
        stream_from_text(markdown),
    )
    return response


async def api_case_restore_tl_event_put(request: Request):
    """Restore case timeline event from trash"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    identity, storage = await prologue(
        request,
        'update_event',
        context={
            'case_guid': case_guid,
            'tl_event_guid': tl_event_guid,
            'case_open_check': True,
        },
    )
    tl_event = await storage.retrieve_tl_event(case_guid, tl_event_guid)
    if not tl_event:
        return json_response(status=404, message="Timeline event not found")
    if tl_event.closes:
        closed_tl_event = await storage.retrieve_tl_event(
            case_guid, tl_event.closes
        )
        if not closed_tl_event:
            return json_response(
                status=400,
                message="Cannot restore timeline event, closed timeline event not found",
            )
        if closed_tl_event.trashed:
            return json_response(
                status=400,
                message="Cannot restore timeline event, closed timeline event needs to be restored first",
            )
        if not await _is_pending(
            storage, case_guid, str(closed_tl_event.guid)
        ):
            return json_response(
                status=400,
                message="Cannot restore timeline event, closes an already closed timeline event",
            )
        await storage.update_tl_event(case_guid, closed_tl_event.guid)
    tl_event = await storage.update_tl_event(
        case_guid, tl_event_guid, {'trashed': False}
    )
    data = {'restored_event': tl_event.to_dict()}
    if tl_event.closes:
        data.update({'closes': str(tl_event.closes)})
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        category='restore_event',
        case=case,
        ext={'user': identity.username, 'data': data},
    )
    return json_response(data=tl_event.to_dict())


async def api_case_star_tl_event_put(request: Request):
    """Star/Unstar case timeline event"""
    case_guid = _get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = _get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    identity, storage = await prologue(
        request,
        'star_event',
        context={'case_guid': case_guid, 'tl_event_guid': tl_event_guid},
    )
    tl_event = await storage.retrieve_tl_event(case_guid, tl_event_guid)
    if not tl_event:
        return json_response(status=404, message="Timeline event not found")
    if tl_event.trashed:
        return json_response(status=400, message="Timeline event is trashed")

    tl_event = await storage.update_tl_event(
        case_guid, tl_event.guid, {'starred': not tl_event.starred}
    )
    data = tl_event.to_dict()
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        category='star_event',
        case=case,
        ext={'user': identity.username, 'data': data},
    )
    return json_response(data=data)


async def api_case_trash_tl_event_put(request: Request):
    """Move case timeline event to trash"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    tl_event_guid = get_guid(request, 'tl_event_guid')
    if not tl_event_guid:
        return json_response(status=400, message="Invalid timeline event GUID")
    identity, storage = await prologue(
        request,
        'trash_event',
        context={
            'case_guid': case_guid,
            'tl_event_guid': tl_event_guid,
            'case_open_check': True,
        },
    )
    tl_event = await storage.retrieve_tl_event(case_guid, tl_event_guid)
    if not tl_event:
        return json_response(status=404, message="Timeline event not found")
    if tl_event.trashed:
        return json_response(
            status=400, message="Timeline event already trashed"
        )
    if tl_event.category == TASK_CATEGORY.name and not await _is_pending(
        storage, case_guid, str(tl_event.guid)
    ):
        return json_response(
            status=400, message="Cannot trash a completed timeline event"
        )
    if tl_event.closes:
        closed_event = await storage.retrieve_tl_event(
            case_guid, tl_event.closes
        )
        if not closed_event:
            return json_response(
                status=404,
                message="Cannot trash event, closed event not found",
            )
        await storage.update_tl_event(
            case_guid, closed_event.guid, {'trashed': True}
        )
    tl_event = await storage.update_tl_event(
        case_guid, tl_event.guid, {'trashed': True}
    )
    data = tl_event.to_dict()
    case = await storage.retrieve_case(case_guid)
    fusion_evt_api = get_fusion_evt_api(request)
    await fusion_evt_api.notify(
        type='trash_event',
        case=case,
        ext={'user': identity.username, 'data': data},
    )
    return json_response(data=data)


async def api_case_trash_get(request: Request):
    """Enumerate case timeline events (trashed)"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    _, storage = await prologue(
        request, 'trashed_events', context={'case_guid': case_guid}
    )
    return json_response(
        data=[
            tl_event.to_dict()
            async for tl_event in storage.enumerate_trashed_tl_events(
                case_guid
            )
        ]
    )


async def api_case_users_get(request: Request):
    """Retrieve case applicable users"""
    case_guid = get_guid(request, 'case_guid')
    if not case_guid:
        return json_response(status=400, message="Invalid case GUID")
    active = 'active' in request.query
    _, storage = await prologue(
        request,
        'case_users',
        context={'case_guid': case_guid, 'active': active},
    )
    case = await storage.retrieve_case(case_guid)
    if not case:
        return json_response(status=404, message="Case not found")
    identities = [
        identity.to_dict()
        async for identity in storage.enumerate_identities()
        if identity.acs.intersection(case.acs)
    ]
    fusion_evt_api = get_fusion_evt_api(request)
    if active:
        usernames = await fusion_evt_api.subscribers(case)
        identities = [
            identity
            for identity in identities
            if identity.username in usernames
        ]
    return json_response(data=identities)


async def api_cases_stats_get(request: Request):
    """Retrieve cases stats (pending/total events)"""
    _, storage = await prologue(request, 'cases_stats', context={})
    return json_response(
        data=[stat.to_dict() async for stat in storage.enumerate_cases_stats()]
    )
