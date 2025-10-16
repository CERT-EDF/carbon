"""Configuration"""

from dataclasses import dataclass

from aiohttp.web import Application, Request
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import Loadable
from edf_fusion.server.auth import FusionAuthAPIConfig
from edf_fusion.server.case import FusionCaseAPIConfig
from edf_fusion.server.config import (
    FusionServerConfig,
    FusionStorageConfig,
    FusionSynchronizerConfig,
)
from edf_fusion.server.constant import FusionConstantAPIConfig
from edf_fusion.server.event import FusionEventAPIConfig
from edf_fusion.server.info import FusionInfoAPIConfig

_LOGGER = get_logger('server.config', root='carbon')
_CARBON_CONFIG = '__carbon_config'


@dataclass(kw_only=True)
class CarbonServerConfig(Loadable):
    """Carbon Server Configuration"""

    server: FusionServerConfig
    storage: FusionStorageConfig
    auth_api: FusionAuthAPIConfig
    case_api: FusionCaseAPIConfig
    info_api: FusionInfoAPIConfig
    event_api: FusionEventAPIConfig
    constant_api: FusionConstantAPIConfig
    synchronizer: FusionSynchronizerConfig

    @classmethod
    def from_dict(cls, dct):
        return cls(
            server=FusionServerConfig.from_dict(dct['server']),
            storage=FusionStorageConfig.from_dict(dct['storage']),
            auth_api=FusionAuthAPIConfig.from_dict(dct['auth_api']),
            case_api=FusionCaseAPIConfig.from_dict(dct['case_api']),
            info_api=FusionInfoAPIConfig.from_dict(dct['info_api']),
            event_api=FusionEventAPIConfig.from_dict(dct['event_api']),
            constant_api=FusionConstantAPIConfig.from_dict(
                dct['constant_api']
            ),
            synchronizer=FusionSynchronizerConfig.from_dict(
                dct['synchronizer']
            ),
        )

    def setup(self, webapp: Application):
        """Register config in webapp context"""
        webapp[_CARBON_CONFIG] = self


def get_carbon_config(app_or_req: Application | Request) -> CarbonServerConfig:
    """Retrieve config from webapp context"""
    if isinstance(app_or_req, Request):
        app_or_req = app_or_req.app
    return app_or_req[_CARBON_CONFIG]
