"""Carbon Category"""

from dataclasses import dataclass, field

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Category(Concept):
    """Carbon Category"""

    name: str
    icon: str
    color: str
    description: str | None = None
    groups: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, dct):
        return cls(
            name=dct['name'],
            icon=dct['icon'],
            color=dct['color'],
            description=dct['description'],
            groups=set(dct.get('groups', [])),
        )

    def to_dict(self):
        return {
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'description': self.description,
            'groups': list(self.groups),
        }

    def update(self, dct):
        self.name = dct.get('name', self.name)
        self.icon = dct.get('icon', self.icon)
        self.color = dct.get('color', self.color)
        self.description = dct.get('description', self.description)
        self.groups = set(dct.get('groups', self.groups))


TASK_CATEGORY = Category(
    name='TASK',
    icon='pending_action',
    color='#993f92',
    description="",
)
