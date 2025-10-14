"""Carbon Timeline Event"""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from edf_fusion.concept import Concept
from edf_fusion.helper.datetime import (
    datetime,
    from_iso,
    from_iso_or_none,
    to_iso,
    to_iso_or_none,
    utcnow,
)


@dataclass(kw_only=True)
class TimelineEvent(Concept):
    """Carbon Timeline Event"""

    guid: UUID = field(default_factory=uuid4)
    title: str
    closes: UUID | None = None
    creator: str
    created: datetime = field(default_factory=utcnow)
    date: datetime
    duedate: datetime | None = None
    starred: bool = False
    trashed: bool = False
    category: str
    assignees: set[str] = field(default_factory=set)
    description: str = ""

    @classmethod
    def from_dict(cls, dct):
        closes = dct['closes']
        if closes:
            closes = UUID(closes)
        return cls(
            guid=UUID(dct['guid']),
            title=dct['title'],
            closes=closes,
            creator=dct['creator'],
            created=from_iso(dct['created']),
            date=from_iso(dct['date']),
            duedate=from_iso_or_none(dct['duedate']),
            starred=dct['starred'],
            trashed=dct['trashed'],
            category=dct['category'],
            assignees=set(dct['assignees']),
            description=dct['description'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'title': self.title,
            'closes': str(self.closes) if self.closes else None,
            'creator': self.creator,
            'created': to_iso(self.created),
            'date': to_iso(self.date),
            'duedate': to_iso_or_none(self.duedate),
            'starred': self.starred,
            'trashed': self.trashed,
            'category': self.category,
            'assignees': list(self.assignees),
            'description': self.description,
        }

    def update(self, dct):
        # guid cannot be updated
        self.title = dct.get('title', self.title)
        closes = dct.get('closes')
        if closes:
            closes = UUID(closes)
        self.closes = closes or self.closes
        # creator cannot be updated
        # created cannot be updated
        self.date = from_iso_or_none(dct.get('date')) or self.date
        self.duedate = from_iso_or_none(dct.get('duedate')) or self.duedate
        self.starred = dct.get('starred', self.starred)
        self.trashed = dct.get('trashed', self.trashed)
        self.category = dct.get('category', self.category)
        self.assignees = set(dct.get('assignees', self.assignees))
        self.description = dct.get('description', self.description)
