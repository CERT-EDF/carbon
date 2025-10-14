"""Carbon Event"""

from dataclasses import dataclass

from edf_fusion.concept import Event as FusionEvent


@dataclass(kw_only=True)
class Event(FusionEvent):
    """Carbon Event"""

    source: str = 'carbon'
