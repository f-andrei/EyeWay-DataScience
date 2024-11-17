#!/bin/bash
set -e

# Start nginx in the background
nginx

# Execute the command passed to docker run (or the default command)
exec "$@"