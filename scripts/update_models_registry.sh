#!/bin/bash
# Fetches latest models from models.dev and saves to bundled registry
curl -s https://models.dev/api.json -o src/tunacode/configuration/models_registry.json
echo "Updated models_registry.json"
