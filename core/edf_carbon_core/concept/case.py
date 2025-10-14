"""Carbon Case"""

from dataclasses import dataclass

from edf_fusion.concept import Case as FusionCase


@dataclass(kw_only=True)
class Case(FusionCase):
    """Carbon Case"""

    utc_display: bool = False

    @classmethod
    def from_dict(cls, dct):
        metadata = super().from_dict(dct)
        metadata.utc_display = dct.get('utc_display')
        return metadata

    def to_dict(self):
        dct = super().to_dict()
        dct.update({'utc_display': self.utc_display})
        return dct

    def update(self, dct):
        super().update(dct)
        self.utc_display = dct.get('utc_display', self.utc_display)
