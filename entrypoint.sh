#!/bin/sh

USER_ID=${LOCAL_USER_ID:-1000}

GROUP_ID=${LOCAL_GROUP_ID:-1050}

addgroup -S mygroup -g $GROUP_ID

adduser -S -g mygroup -u $USER_ID myuser

exec su-exec $USER_ID:$GROUP_ID "$@"
