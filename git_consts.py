# File: git_consts.py
#
# Copyright (c) 2017-2024 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
GIT_CONFIG_REPO_URI = "repo_uri"
GIT_CONFIG_REPO_NAME = "repo_name"
GIT_CONFIG_BRANCH_NAME = "branch_name"
GIT_CONFIG_USERNAME = "username"
GIT_CONFIG_PASSWORD = "password"  # pragma: allowlist secret
GIT_CONNECTION_TEST_MSG = "Querying to verify the repo URI"
GIT_TEST_CONNECTIVITY_FAIL = "Connectivity test failed"
GIT_TEST_CONNECTIVITY_SUCCESS = "Connectivity test succeeded"
GIT_INVALID_URI_TYPE = "App only supports http(s) URI"
GIT_USERNAME_AND_PASSWORD_REQUIRED = "Username and password are required in case of http(s) URI"  # pragma: allowlist secret
GIT_URL_OR_CONFIG_REQUIRED = "You must either provide a URL to clone or configure the app with required information"
