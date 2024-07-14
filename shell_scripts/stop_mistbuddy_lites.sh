#!/bin/bash

curl -X 'GET' \
  'http://192.168.68.113:8080/api/v1/mistbuddy-lite/stop' \
  -H 'accept: application/json'