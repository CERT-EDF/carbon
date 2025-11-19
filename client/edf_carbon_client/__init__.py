"""Carbon Client"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from aiohttp import FormData
from edf_carbon_core.concept import (
    CaseStats,
    Category,
    Notification,
    TimelineEvent,
)
from edf_fusion.client import FusionClient
from edf_fusion.concept import Identity, PendingDownloadKey
from edf_fusion.helper.logging import get_logger

_LOGGER = get_logger('client', root='carbon')


@dataclass(kw_only=True)
class CarbonClient:
    """Carbon Client"""

    fusion_client: FusionClient

    async def subscribe(self, case_guid: UUID) -> AsyncIterator[Notification]:
        """Subscribe"""
        _LOGGER.info("subscribing to case %s", case_guid)
        endpoint = f'/api/case/{case_guid}/subscribe'
        async for notif in self.fusion_client.sse(
            endpoint, concept_cls=Notification
        ):
            yield notif

    async def create_case_tl_event(
        self, case_guid: UUID, tl_event: TimelineEvent
    ) -> TimelineEvent | None:
        """Create case timeline event"""
        _LOGGER.info("creating event in case %s", case_guid)
        endpoint = f'/api/case/{case_guid}/event'
        return await self.fusion_client.post(
            endpoint, tl_event, concept_cls=TimelineEvent
        )

    async def update_case_tl_event(
        self, case_guid: UUID, tl_event: TimelineEvent
    ) -> TimelineEvent | None:
        """Update case timeline event"""
        _LOGGER.info("updating event %s in case %s", tl_event.guid, case_guid)
        endpoint = f'/api/case/{case_guid}/event/{tl_event.guid}'
        return await self.fusion_client.put(
            endpoint, tl_event, concept_cls=TimelineEvent
        )

    async def delete_case_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> bool:
        """Delete case timeline event"""
        _LOGGER.info("deleting event %s in case %s", tl_event_guid, case_guid)
        endpoint = f'/api/case/{case_guid}/event/{tl_event_guid}'
        return await self.fusion_client.delete(endpoint)

    async def trash_case_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> TimelineEvent | None:
        """Trash case timeline event"""
        _LOGGER.info("trashing event %s in case %s", tl_event_guid, case_guid)
        endpoint = f'/api/case/{case_guid}/event/{tl_event_guid}/trash'
        return await self.fusion_client.put(
            endpoint, concept_cls=TimelineEvent
        )

    async def star_case_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> TimelineEvent | None:
        """Trash case timeline event"""
        _LOGGER.info("star-ing event %s in case %s", tl_event_guid, case_guid)
        endpoint = f'/api/case/{case_guid}/event/{tl_event_guid}/star'
        return await self.fusion_client.put(
            endpoint, concept_cls=TimelineEvent
        )

    async def restore_case_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> TimelineEvent | None:
        """Restore case timeline event"""
        _LOGGER.info("restoring event %s in case %s", tl_event_guid, case_guid)
        endpoint = f'/api/case/{case_guid}/event/{tl_event_guid}/restore'
        return await self.fusion_client.put(
            endpoint, concept_cls=TimelineEvent
        )

    async def retrieve_case_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> TimelineEvent | None:
        """Retrieve case timeline event"""
        endpoint = f'/api/case/{case_guid}/event/{tl_event_guid}'
        return await self.fusion_client.get(
            endpoint, concept_cls=TimelineEvent
        )

    async def retrieve_case_users(
        self, case_guid: UUID, active: bool = False
    ) -> list[Identity] | None:
        """Retrieve case users"""
        endpoint = f'/api/case/{case_guid}/users'
        kwargs = {}
        if active:
            kwargs['params'] = {'active': ''}
        return await self.fusion_client.get(
            endpoint, concept_cls=Identity, **kwargs
        )

    async def retrieve_case_tl_events(
        self, case_guid: UUID
    ) -> list[TimelineEvent] | None:
        """Retrieve case timeline events (not trashed)"""
        endpoint = f'/api/case/{case_guid}/events'
        return await self.fusion_client.get(
            endpoint, concept_cls=TimelineEvent
        )

    async def export_case_tl_events(
        self,
        case_guid: UUID,
        output: Path,
        fields: list[str] | None = None,
        starred: bool = False,
    ) -> Path | None:
        """Export case timeline event"""
        _LOGGER.info("exporting events in case %s", case_guid)
        endpoint = f'/api/case/{case_guid}/events/export'
        fields = fields or []
        params = [('fields', field) for field in fields]
        if starred:
            params.append(('starred', ''))
        return await self.fusion_client.download(
            endpoint, output, params=params
        )

    async def retrieve_case_categories(
        self, case_guid: UUID
    ) -> list[Category] | None:
        """Retrieve case categories"""
        endpoint = f'/api/case/{case_guid}/categories'
        return await self.fusion_client.get(endpoint, concept_cls=Category)

    async def retrieve_case_trashed_tl_events(
        self, case_guid: UUID
    ) -> list[TimelineEvent] | None:
        """Retrieve case timeline events (trashed)"""
        endpoint = f'/api/case/{case_guid}/trash'
        return await self.fusion_client.get(
            endpoint, concept_cls=TimelineEvent
        )

    async def retrieve_case_stats(self) -> list[CaseStats] | None:
        """Retrieve case stats"""
        endpoint = '/api/cases/stats'
        return await self.fusion_client.get(endpoint, concept_cls=CaseStats)
