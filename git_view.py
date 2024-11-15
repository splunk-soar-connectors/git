# File: git_view.py
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
def _get_git_status_ctx(result):
    ctx_result = {}
    data = result.get_data()

    if not data:
        ctx_result["data"] = {}

    data = data[0]

    line_ctx = []
    files = []
    staged = data.get("staged", {})
    unstaged = data.get("unstaged", {})
    untracked = data.get("untracked_files", [])
    for k, v in staged.items():
        if isinstance(v, list):
            for i in v:
                files.append(i)
    for k, v in unstaged.items():
        if isinstance(v, list):
            for i in v:
                files.append(i)
    for i in untracked:
        files.append(i)

    for line in data["output"].splitlines():
        for f in files:
            if f in line:
                parts = line.split(f, 1)
                contains = "->" in f
                if contains:
                    parts2 = f.split("->")
                    f = parts2[0] + " -> "
                    parts[1] = parts2[1].strip()
                line_ctx.append({"content": parts[0], "endline": False, "contains": False})
                line_ctx.append({"content": f, "endline": False, "contains": not contains})
                line_ctx.append({"content": parts[1], "endline": True, "contains": contains})
                break
        else:
            line_ctx.append({"content": line, "endline": True, "contains": False})

    ctx_result["line_ctx"] = line_ctx
    return ctx_result


def _get_ctx_result(result):
    ctx_result = {}

    param = result.get_param()
    summary = result.get_summary()
    data = result.get_data()

    ctx_result["param"] = param

    if summary:
        ctx_result["summary"] = summary

    if not data:
        ctx_result["data"] = {}
        return ctx_result

    ctx_result["data"] = data[0]

    return ctx_result


# Function to provide custom view for all actions
def display_action_details(provides, all_app_runs, context):
    context["results"] = results = []

    for summary, action_results in all_app_runs:
        for result in action_results:
            ctx_result = _get_ctx_result(result)
            if not ctx_result:
                continue
            results.append(ctx_result)

    return "git_list_repos.html"


def display_git_status(provides, all_app_runs, context):
    context["results"] = results = []
    for summary, action_results in all_app_runs:
        for result in action_results:
            ctx_result = _get_git_status_ctx(result)
            if not ctx_result:
                continue
            results.append(ctx_result)

    return "git_git_status.html"
