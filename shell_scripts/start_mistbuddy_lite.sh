#!/bin/bash

curl --location "http://127.0.0.1:8085/api/v1/start" --header "Content-Type: application/json" --data "{
    \"tent_name\": \"tent_one\",
    \"duration_on\": 6
}"