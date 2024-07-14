#!/bin/bash

curl -X 'POST' \
  'http://192.168.68.113:8080/api/v1/mistbuddy-lite/start' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "duration_on": 8,
  "name": "tent_one"
}'