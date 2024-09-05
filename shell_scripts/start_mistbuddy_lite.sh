#!/bin/bash

curl --location "http://beanie.local:8085/api/v1/start" --header "Content-Type: application/json" --data "{
    \"tent_name\": \"tent_one\",
    \"duration_on\": 6
}"