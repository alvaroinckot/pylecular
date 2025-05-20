import datetime
import logging
import sys

import structlog

LOG_LEVEL_MAP = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_parsed_log_level(log_level):
    return LOG_LEVEL_MAP.get(log_level, logging.INFO)


def moleculer_format_renderer(_, __, event_dict):
    timestamp = datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds") + "Z"
    level = event_dict.pop("level", "INFO").upper()
    node = event_dict.pop("node", "<unknown>")
    service = event_dict.pop("service", "<unspecified>")
    message = event_dict.pop("event", "")
    return f"[{timestamp}] {level:<5} {node}/{service}: {message}"


def get_logger(log_level, log_format="PLAIN"):
    log_level = get_parsed_log_level(log_level=log_level)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
    ]

    if log_format == "JSON":
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ]  # type: ignore
        )
    else:
        processors.append(moleculer_format_renderer)  # type: ignore

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        processors=processors,
    )

    return structlog.get_logger()
