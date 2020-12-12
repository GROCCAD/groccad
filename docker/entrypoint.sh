#!/usr/bin/env bash

echo "Resetting DB and running migrations..."
fab reset_and_migrate

echo "Loadings terms..."
fab load_terms

exec "$@"