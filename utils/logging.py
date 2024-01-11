# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict
from fastapi import Request
import structlog

from utils import metadata

def field_name_modifier(
    logger: structlog._loggers.PrintLogger, log_method: str, event_dict: Dict
) -> Dict:
    """Changes the keys for some of the fields,
    to match Cloud Logging's expectations
    https://cloud.google.com/run/docs/logging#special-fields
    """
    # structlog example adapted from
    # https://github.com/ymotongpoo/cloud-logging-configurations/blob/master/python/structlog/main.py

    event_dict["severity"] = event_dict["level"]
    del event_dict["level"]

    if "event" in event_dict:
        event_dict["message"] = event_dict["event"]
        del event_dict["event"]
    return event_dict


def trace_modifier(logger, log_method, event_dict, request: Request = None):
    """Adds Tracing correlation adapted for FastAPI"""
    if request:
        trace_header = request.headers.get("X-Cloud-Trace-Context")
        if trace_header:
            trace = trace_header.split("/")
            project = metadata.get_project_id()
            event_dict["logging.googleapis.com/trace"] = f"projects/{project}/traces/{trace[0]}"
    return event_dict

def getJSONLogger(request: Request = None) -> structlog.BoundLogger:
    """Create a JSON logger for FastAPI"""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            field_name_modifier,
            lambda logger, log_method, event_dict: trace_modifier(logger, log_method, event_dict, request),
            structlog.processors.TimeStamper("iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    return structlog.get_logger()



logger = getJSONLogger()


def flush() -> None:
    # Setting PYTHONUNBUFFERED in Dockerfile/Buildpack ensured no buffering

    # https://docs.python.org/3/library/logging.html#logging.shutdown
    # When the logging module is imported, it registers this
    # function as an exit handler (see atexit), so normally
    # there’s no need to do that manually.
    pass
