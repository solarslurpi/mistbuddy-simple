#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################################
# Author: Margaret Johnson
# Copyright (c) 2024 Margaret Johnson
###########################################################################################

class AppException(Exception):
    """Base exception class for the application."""
    def __init__(self, message="An error occurred"):
        self.message = message
        super().__init__(self.message)

class MQTTSetupError(AppException):
    """Should have try/except whenever publishing an mqtt message."""
    def __init__(self, message="Error setting up the MQTT client"):
        super().__init__(message)

class MQTTPublishError(AppException):
    """Should have try/except whenever publishing an mqtt message."""
    def __init__(self, message="Error publishing an MQTT message"):
        super().__init__(message)

class MQTTConnectionError(AppException):
    """Client connection failed within mqtt_code."""
    def __init__(self, message="Failed to connect to the MQTT broker."):
        super().__init__(message)
