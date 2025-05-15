import datetime
import logging
import sys
import structlog


def moleculer_format_renderer(_, __, event_dict):
    timestamp = datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    level = event_dict.pop("level", "INFO").upper()
    node = event_dict.pop("node", "<unknown>")
    service = event_dict.pop("service", "<unspecified>")
    message = event_dict.pop("event", "")

    return f"[{timestamp}] {level:<5} {node}/{service}: {message}"

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# TODO: change format by config
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        moleculer_format_renderer,
#         structlog.processors.TimeStamper(fmt="iso"),
#         structlog.processors.format_exc_info,
#         structlog.processors.LogfmtRenderer(),
#         structlog.processors.JSONRenderer(),
    ],
)

