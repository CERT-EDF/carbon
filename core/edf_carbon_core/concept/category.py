"""Carbon Category"""

from dataclasses import dataclass, field

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class Category(Concept):
    """Carbon Category"""

    name: str
    icon: str
    template: str | None = None
    groups: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, dct):
        return cls(
            name=dct['name'],
            icon=dct['icon'],
            template=dct['template'],
            groups=set(dct.get('groups', [])),
        )

    def to_dict(self):
        return {
            'name': self.name,
            'icon': self.icon,
            'template': self.template,
            'groups': list(self.groups),
        }

    def update(self, dct):
        self.name = dct.get('name', self.name)
        self.icon = dct.get('icon', self.icon)
        self.template = dct.get('template', self.template)
        self.groups = set(dct.get('groups', self.groups))


TASK_CATEGORY = Category(name='TASK', icon='pending_action')
