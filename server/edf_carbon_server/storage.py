"""Carbon Storage"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from aiohttp.web import Application
from aiosqlite import Connection, Error, Row, connect
from edf_carbon_core.concept import Case, CaseStats, TimelineEvent
from edf_fusion.concept import Concept, Identity
from edf_fusion.helper.datetime import (
    from_iso,
    from_iso_or_none,
    to_iso,
    utcnow,
)
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import dump_json, load_json
from edf_fusion.server.storage import FusionStorage

from .config import FusionStorageConfig

_LOGGER = get_logger('server.storage', root='carbon')
_MODEL_VERSION = 1
_CREATE_TABLE_CASE = f'''
CREATE TABLE IF NOT EXISTS case_{_MODEL_VERSION} (
    guid TEXT PRIMARY KEY,
    managed INTEGER,
    created TEXT,
    updated TEXT,
    closed TEXT,
    tsid TEXT,
    name TEXT,
    description TEXT,
    acs TEXT,
    utc_display INTEGER
)
'''
_CREATE_TABLE_EVENT = f'''
CREATE TABLE IF NOT EXISTS event_{_MODEL_VERSION} (
    guid TEXT PRIMARY KEY,
    case_guid TEXT,
    title TEXT,
    closes TEXT,
    creator TEXT,
    created TEXT,
    date TEXT,
    duedate TEXT,
    starred INTEGER,
    trashed INTEGER,
    category TEXT,
    assignees TEXT,
    description TEXT
)
'''
_CREATE_INDEX_EVENT = f'''
CREATE INDEX IF NOT EXISTS event_{_MODEL_VERSION}_idx
ON event_{_MODEL_VERSION} (case_guid, closes)
'''
_ATTACH_CASE = f'''
UPDATE case_{_MODEL_VERSION}
SET guid = :next_guid, managed = 1
WHERE guid = :guid
'''
_ATTACH_TL_EVENT = f'''
UPDATE event_{_MODEL_VERSION}
SET case_guid = :next_guid
WHERE case_guid = :guid
'''
_REPLACE_CASE = f'''
REPLACE INTO case_{_MODEL_VERSION} VALUES (
    :guid,
    :managed,
    :created,
    :updated,
    :closed,
    :tsid,
    :name,
    :description,
    :acs,
    :utc_display
)
'''
_REPLACE_TL_EVENT = f'''
REPLACE INTO event_{_MODEL_VERSION} VALUES (
    :guid,
    :case_guid,
    :title,
    :closes,
    :creator,
    :created,
    :date,
    :duedate,
    :starred,
    :trashed,
    :category,
    :assignees,
    :description
)
'''
_DELETE_CASE = f'''
DELETE FROM case_{_MODEL_VERSION}
WHERE guid = :guid
'''
_DELETE_TL_EVENT_ONE = f'''
DELETE FROM event_{_MODEL_VERSION}
WHERE guid = :guid AND case_guid = :case_guid
'''
_DELETE_TL_EVENT_ALL = f'''
DELETE FROM event_{_MODEL_VERSION}
WHERE case_guid = :case_guid
'''
_SELECT_CASE_ALL = f'SELECT * FROM case_{_MODEL_VERSION}'
_SELECT_CASE_ONE = f'''
SELECT * FROM case_{_MODEL_VERSION}
WHERE guid = :guid
'''
_SELECT_CASES_STATS = f'''
SELECT e.case_guid AS guid,
    SUM(CASE WHEN e.trashed THEN 0 ELSE 1 END) AS total,
    SUM(CASE WHEN e.category = 'TASK' AND NOT e.trashed
        AND NOT EXISTS (
            SELECT 1 FROM event_{_MODEL_VERSION} AS close
                WHERE NOT close.trashed
                AND close.closes IS NOT NULL
                AND close.closes = e.guid
            )
        THEN 1
        ELSE 0
    END) AS pending
FROM event_{_MODEL_VERSION} AS e
GROUP BY e.case_guid
'''
_SELECT_TL_EVENT_CLOSED = f'''
SELECT closes FROM event_{_MODEL_VERSION}
WHERE case_guid = :case_guid AND closes IS NOT NULL
'''
_SELECT_TL_EVENT_ONE = f'''
SELECT * FROM event_{_MODEL_VERSION}
WHERE guid = :guid AND case_guid = :case_guid
'''
_SELECT_TL_EVENT_ALL = f'''
SELECT * FROM event_{_MODEL_VERSION}
WHERE case_guid = :case_guid AND trashed = 0
'''
_SELECT_TL_EVENT_TRASHED = f'''
SELECT * FROM event_{_MODEL_VERSION}
WHERE case_guid = :case_guid AND trashed = 1
'''


async def _init_db(connection: Connection):
    _LOGGER.info("initialize database...")
    async with connection.cursor() as cursor:
        for statement in (
            _CREATE_TABLE_CASE,
            _CREATE_TABLE_EVENT,
            _CREATE_INDEX_EVENT,
        ):
            await cursor.execute(statement)
    _LOGGER.info("database initialized.")


def _parameters_from_concept(concept: Concept) -> dict:
    dct = concept.to_dict()
    parameters = {}
    for key, val in dct.items():
        if isinstance(val, (int, float, str, bytes)) or val is None:
            parameters[key] = val
            continue
        if isinstance(val, (list, dict)):
            parameters[key] = dump_json(val)
            continue
        if isinstance(val, bool):
            parameters[key] = 1 if val else 0
    return parameters


def _case_from_row(row: Row) -> Case:
    return Case(
        guid=UUID(row['guid']),
        managed=bool(row['managed']),
        created=from_iso(row['created']),
        updated=from_iso_or_none(row['updated']),
        closed=from_iso_or_none(row['closed']),
        tsid=row['tsid'],
        name=row['name'],
        description=row['description'],
        acs=set(load_json(row['acs'])),
        utc_display=bool(row['utc_display']),
    )


def _tl_event_from_row(row: Row) -> TimelineEvent:
    closes = row['closes']
    if closes:
        closes = UUID(closes)
    return TimelineEvent(
        guid=UUID(row['guid']),
        title=row['title'],
        closes=closes,
        creator=row['creator'],
        created=from_iso(row['created']),
        date=from_iso(row['date']),
        duedate=from_iso_or_none(row['duedate']),
        starred=bool(int(row['starred'])),
        trashed=bool(int(row['trashed'])),
        category=row['category'],
        assignees=set(load_json(row['assignees'])),
        description=row['description'],
    )


def _identity_from_row(row: Row) -> Identity:
    return Identity(
        username=row['username'], groups=set(load_json(row['groups']))
    )


@dataclass(kw_only=True)
class Storage(FusionStorage):
    """Storage"""

    config: FusionStorageConfig
    _connection: Connection | None = None

    async def _execute(self, statement: str, parameters: dict | None = None):
        parameters = parameters or {}
        async with self._connection.execute(statement, parameters) as cursor:
            await cursor.close()

    async def _fetchone(
        self, statement: str, parameters: dict | None = None
    ) -> Row | None:
        parameters = parameters or {}
        async with self._connection.execute(statement, parameters) as cursor:
            row = await cursor.fetchone()
            await cursor.close()
            return row

    async def _fetchmany(
        self, statement: str, parameters: dict | None = None
    ) -> AsyncIterator[Row]:
        parameters = parameters or {}
        async with self._connection.execute(statement, parameters) as cursor:
            async for row in cursor:
                yield row
            await cursor.close()

    async def context(self, webapp: Application):
        _LOGGER.info("sqlite storage starting up.")
        database = self.config.directory / 'carbon.db'
        async with connect(database, autocommit=True) as connection:
            self._connection = connection
            self._connection.row_factory = Row
            await _init_db(self._connection)
            yield
            _LOGGER.info("sqlite storage cleaning up.")
            await self._connection.close()
            self._connection = None

    async def attach_case(self, case_guid: UUID, next_case_guid: UUID) -> bool:
        case = await self.retrieve_case(case_guid)
        if not case:
            _LOGGER.warning("cannot attach missing case: %s", case_guid)
            return False
        if case.managed:
            _LOGGER.warning(
                "prevented an attempt to attach a managed case: %s => %s",
                case_guid,
                next_case_guid,
            )
            return False
        parameters = {'guid': case_guid, 'next_guid': next_case_guid}
        try:
            await self._execute(_ATTACH_TL_EVENT, parameters)
            await self._execute(_ATTACH_CASE, parameters)
        except Error:
            _LOGGER.exception("failed to attach case")
            return False
        case = await self.retrieve_case(next_case_guid)
        if not case:
            return False
        return True

    async def create_case(self, managed: bool, dct) -> Case | None:
        if managed:
            dct['managed'] = True
            case = Case.from_dict(dct)
        else:
            try:
                case = Case(
                    tsid=dct.get('tsid'),
                    name=dct['name'],
                    description=dct['description'],
                    acs=set(dct.get('acs', [])),
                    utc_display=dct.get('utc_display', False),
                )
            except KeyError:
                return None
        parameters = _parameters_from_concept(case)
        try:
            await self._execute(_REPLACE_CASE, parameters)
        except Error:
            _LOGGER.exception("failed to create case")
            return None
        return case

    async def update_case(self, case_guid: UUID, dct) -> Case | None:
        case = await self.retrieve_case(case_guid)
        if not case:
            return None
        case.update(dct)
        parameters = _parameters_from_concept(case)
        try:
            await self._execute(_REPLACE_CASE, parameters)
        except Error:
            _LOGGER.exception("failed to update case")
            return None
        return case

    async def delete_case(self, case_guid: UUID) -> bool:
        parameters = {'case_guid': str(case_guid)}
        try:
            await self._execute(_DELETE_TL_EVENT_ALL, parameters)
        except Error:
            _LOGGER.exception("failed to delete case events")
            return False
        parameters = {'guid': str(case_guid)}
        try:
            await self._execute(_DELETE_CASE, parameters)
        except Error:
            _LOGGER.exception("failed to delete case")
            return False
        return True

    async def retrieve_case(self, case_guid: UUID) -> Case | None:
        parameters = {'guid': str(case_guid)}
        try:
            row = await self._fetchone(_SELECT_CASE_ONE, parameters)
        except Error:
            _LOGGER.exception("failed to retrieve case")
            return None
        if row is None:
            _LOGGER.error("case not found: %s", case_guid)
            return None
        case = _case_from_row(row)
        return case

    async def enumerate_cases(self) -> AsyncIterator[Case]:
        try:
            async for row in self._fetchmany(_SELECT_CASE_ALL):
                case = _case_from_row(row)
                yield case
        except Error:
            _LOGGER.exception("failed to retrieve all cases")
            return

    async def create_tl_event(
        self, case_guid: UUID, dct
    ) -> TimelineEvent | None:
        """Create timeline event"""
        closes = dct.get('closes')
        if closes:
            closes = UUID(closes)
        tl_event_date = dct.get('date')
        if not tl_event_date:
            tl_event_date = to_iso(utcnow())
        try:
            tl_event = TimelineEvent(
                title=dct['title'],
                closes=closes,
                creator=dct['creator'],
                date=from_iso(tl_event_date),
                duedate=from_iso_or_none(dct.get('duedate')),
                starred=dct.get('starred', False),
                trashed=dct.get('trashed', False),
                category=dct['category'],
                assignees=set(dct.get('assignees', [])),
                description=dct.get('description', ''),
            )
        except KeyError:
            _LOGGER.exception("failed to create timeline event")
            return None
        parameters = _parameters_from_concept(tl_event)
        parameters['case_guid'] = str(case_guid)
        try:
            await self._execute(_REPLACE_TL_EVENT, parameters)
        except Error:
            _LOGGER.exception("failed to create timeline event")
            return None
        return tl_event

    async def update_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID, dct
    ) -> TimelineEvent | None:
        """Update timeline event"""
        tl_event = await self.retrieve_tl_event(case_guid, tl_event_guid)
        if not tl_event:
            return None
        tl_event.update(dct)
        parameters = _parameters_from_concept(tl_event)
        parameters['case_guid'] = str(case_guid)
        try:
            await self._execute(_REPLACE_TL_EVENT, parameters)
        except Error:
            _LOGGER.exception("failed to update timeline event")
            return None
        return tl_event

    async def delete_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> bool:
        """Delete timeline event"""
        parameters = {'guid': str(tl_event_guid), 'case_guid': str(case_guid)}
        try:
            await self._execute(_DELETE_TL_EVENT_ONE, parameters)
        except Error:
            _LOGGER.exception("failed to delete timeline event")
            return False
        return True

    async def retrieve_tl_event(
        self, case_guid: UUID, tl_event_guid: UUID
    ) -> TimelineEvent | None:
        """Retrieve timeline event"""
        parameters = {'guid': str(tl_event_guid), 'case_guid': str(case_guid)}
        try:
            row = await self._fetchone(_SELECT_TL_EVENT_ONE, parameters)
        except Error:
            _LOGGER.exception("failed to retrieve timeline event")
            return None
        if row is None:
            _LOGGER.error("event not found: %s", tl_event_guid)
            return None
        tl_event = _tl_event_from_row(row)
        return tl_event

    async def retrieve_closed_tl_events(
        self, case_guid: UUID
    ) -> AsyncIterator[str]:
        """Retrieve closed timeline events"""
        parameters = {'case_guid': str(case_guid)}
        try:
            async for row in self._fetchmany(
                _SELECT_TL_EVENT_CLOSED, parameters
            ):
                yield row['closes']
        except Error:
            _LOGGER.exception("failed to retrieve closed timeline events")
            return

    async def enumerate_tl_events(
        self, case_guid: UUID
    ) -> AsyncIterator[TimelineEvent]:
        """Enumerate timeline events"""
        parameters = {'case_guid': str(case_guid)}
        try:
            async for row in self._fetchmany(_SELECT_TL_EVENT_ALL, parameters):
                tl_event = _tl_event_from_row(row)
                yield tl_event
        except Error:
            _LOGGER.exception("failed to retrieve all timeline events")
            return

    async def enumerate_trashed_tl_events(
        self, case_guid: UUID
    ) -> AsyncIterator[TimelineEvent]:
        """Enumerate trashed timeline event"""
        parameters = {'case_guid': str(case_guid)}
        try:
            async for row in self._fetchmany(
                _SELECT_TL_EVENT_TRASHED, parameters
            ):
                tl_event = _tl_event_from_row(row)
                yield tl_event
        except Error:
            _LOGGER.exception("failed to retrieve trashed timeline events")
            return

    async def enumerate_cases_stats(self) -> AsyncIterator[CaseStats]:
        """Enumerate case statistics"""
        try:
            async for row in self._fetchmany(_SELECT_CASES_STATS):
                case = CaseStats(
                    guid=UUID(row['guid']),
                    pending=row['pending'],
                    total=row['total'],
                )
                yield case
        except Error:
            _LOGGER.exception("failed to retrieve cases stats")
            return
