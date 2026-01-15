#!/bin/bash
set -e

SERVICE=$1

if [ -z "$SERVICE" ]; then
  echo "Error: Service name required"
  echo "Usage: /rebuild <service>"
  echo "Services: analyst, config, rag_queen_api"
  exit 1
fi

echo "Triggering rebuild for $SERVICE service in Tilt..."
tilt trigger "$SERVICE"
echo "Rebuild triggered. Check Tilt UI at http://localhost:10350 for progress."
