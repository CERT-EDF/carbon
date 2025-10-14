#!/usr/bin/env sh
set -e
# prepare data directory if needed
mkdir -p /data
# prepare configuration directory if needed
mkdir -p /conf
if [ ! -f /conf/carbon.yml ]; then
    cp /tpl/carbon.dist.yml /conf/carbon.yml
fi
if [ ! -f /conf/constant.yml ]; then
    cp /tpl/constant.dist.yml /conf/constant.yml
fi
# prepare analyzer directory if needed
mkdir -p /analyzer
# exec depending on ROLE
case "${ROLE}" in
    server)
        exec /venv/bin/carbon-server --config /conf/carbon.yml
        ;;
    synchronizer)
        exec /venv/bin/carbon-synchronizer --config /conf/carbon.yml
        ;;
    *)
        exec "$@"
        ;;
esac
