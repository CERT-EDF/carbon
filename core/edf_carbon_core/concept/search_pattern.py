"""Carbon SearchPattern"""

from dataclasses import dataclass

from edf_fusion.concept import Concept


@dataclass(kw_only=True)
class SearchPattern(Concept):
    """Carbon SearchPattern"""

    name: str
    pattern: str

    @classmethod
    def from_dict(cls, dct):
        return cls(name=dct['name'], pattern=dct['pattern'])

    def to_dict(self):
        return {'name': self.name, 'pattern': self.pattern}

    def update(self, dct):
        self.name = dct.get('name', self.name)
        self.pattern = dct.get('pattern', self.pattern)
