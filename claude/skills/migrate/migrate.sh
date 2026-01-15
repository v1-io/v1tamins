#!/bin/bash
set -e

ACTION=$1
SERVICE=$2
shift 2

if [ -z "$ACTION" ] || [ -z "$SERVICE" ]; then
  echo "Error: Action and service name required"
  echo ""
  echo "Usage:"
  echo "  /migrate create <service> <description>"
  echo "  /migrate apply <service>"
  echo ""
  echo "Services: analyst, config, artifact, rag_queen"
  exit 1
fi

case "$ACTION" in
  create)
    DESCRIPTION="$*"
    if [ -z "$DESCRIPTION" ]; then
      echo "Error: Migration description required"
      echo "Usage: /migrate create <service> <description>"
      exit 1
    fi
    echo "Creating migration for $SERVICE: $DESCRIPTION"
    commander makemigrations "$SERVICE" -m "$DESCRIPTION"
    ;;
  apply)
    echo "Applying migrations for $SERVICE..."
    commander upgrade "$SERVICE"
    ;;
  *)
    echo "Error: Unknown action '$ACTION'"
    echo "Valid actions: create, apply"
    exit 1
    ;;
esac
