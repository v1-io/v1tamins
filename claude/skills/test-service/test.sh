#!/bin/bash
set -e

SERVICE=$1
shift

if [ -z "$SERVICE" ]; then
  echo "Error: Service name required"
  echo "Usage: /test-service <service> [options]"
  echo "Services: analyst, config, rag_queen, common"
  exit 1
fi

echo "Running tests for $SERVICE service..."
commander test "$SERVICE" "$@"
