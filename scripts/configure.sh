#!/bin/bash
sleep 60
curl -X POST http://localhost:5601/api/saved_objects/_import?overwrite=true \
