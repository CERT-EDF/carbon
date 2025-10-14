"""Carbon Case Synchronizer"""

from argparse import ArgumentParser
from pathlib import Path

from edf_fusion.concept import Case
from edf_fusion.helper.logging import get_logger
from edf_fusion.helper.serializing import dump_json
from edf_fusion.server.storage import SyncStorage
from edf_fusion.server.synchronizer import FusionSynchronizer

from .__version__ import version
from .config import CarbonServerConfig
from .storage import Storage

_LOGGER = get_logger('synchronizer', root='carbon')


async def _sync_case_impl(storage: Storage, case: Case, directory: Path):
    sync_storage = SyncStorage(case=case, directory=directory)
    case_journal = sync_storage.reports / 'carbon_events.jsonl'
    with case_journal.open('w', encoding='utf-8') as fobj:
        async for tl_event in storage.enumerate_tl_events(case.guid):
            fobj.write(dump_json(tl_event.to_dict()))
            fobj.write('\n')


def _parse_args():
    parser = ArgumentParser(description="Carbon Synchronizer")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('carbon.yml'),
        help="Configuration file",
    )
    return parser.parse_args()


def app():
    """Application entrypoint"""
    _LOGGER.info("Carbon Synchronizer %s", version)
    args = _parse_args()
    config = CarbonServerConfig.from_filepath(args.config)
    synchronizer = FusionSynchronizer(
        config=config.synchronizer,
        storage=Storage(config=config.storage),
        sync_case_impl=_sync_case_impl,
    )
    synchronizer.run()


if __name__ == '__main__':
    app()
