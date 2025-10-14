"""Carbon Case Stats"""

from dataclasses import dataclass
from uuid import UUID

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class CaseStats(Concept):
    """Carbon Case"""

    guid: UUID
    pending: int
    total: int

    @classmethod
    def from_dict(cls, dct):
        return cls(
            guid=UUID(dct['guid']),
            pending=dct['pending'],
            total=dct['total'],
        )

    def to_dict(self):
        return {
            'guid': str(self.guid),
            'pending': self.pending,
            'total': self.total,
        }

    def update(self, dct):
        raise NotImplementedError("CaseStat.update shall not be called")
