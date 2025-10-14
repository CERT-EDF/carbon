"""Carbon Notification"""

from dataclasses import dataclass, field
from uuid import UUID

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Notification(Concept):
    """Carbon Notification"""

    type: str
    user: str
    case_guid: UUID
    data: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, dct):
        return cls(
            type=dct['type'],
            user=dct['user'],
            case_guid=UUID(dct['case_guid']),
            data=dct['data'],
        )

    def to_dict(self):
        return {
            'type': self.type,
            'user': self.user,
            'case_guid': str(self.case_guid),
            'data': self.data,
        }

    def update(self, dct):
        raise NotImplementedError("Notification.update shall not be called")
