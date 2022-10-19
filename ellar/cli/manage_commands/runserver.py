import os
import ssl
import sys
import typing as t
from pathlib import Path

import typer
from h11._connection import DEFAULT_MAX_INCOMPLETE_EVENT_SIZE
from uvicorn.config import (
    HTTP_PROTOCOLS,
    INTERFACES,
    LIFESPAN,
    LOGGING_CONFIG,
    LOOP_SETUPS,
    SSL_PROTOCOL_VERSION,
    WS_PROTOCOLS,
)
from uvicorn.main import run as uvicorn_run

from ellar.constants import ELLAR_CONFIG_MODULE, ELLAR_META, LOG_LEVELS
from ellar.core import Config
from ellar.helper.enums import create_enums_from_list

from ..service import EllarCLIException, EllarCLIService

__all__ = ["runserver"]


HTTP_CHOICES = create_enums_from_list("HTTP_CHOICES", *list(HTTP_PROTOCOLS.keys()))
WS_CHOICES = create_enums_from_list("WS_CHOICES", *list(WS_PROTOCOLS.keys()))
LIFESPAN_CHOICES = create_enums_from_list("LIFESPAN_CHOICES", *list(LIFESPAN.keys()))
LOOP_CHOICES = create_enums_from_list(
    "LOOP_CHOICES", *[key for key in LOOP_SETUPS.keys() if key != "none"]
)
INTERFACE_CHOICES = create_enums_from_list("INTERFACES", *INTERFACES)


def runserver(
    ctx: typer.Context,
    host: str = typer.Option(
        "127.0.0.1", help="Bind socket to this host.", show_default=True
    ),
    port: int = typer.Option(8000, help="Bind socket to this port.", show_default=True),
    uds: t.Optional[str] = typer.Option(None, help="Bind to a UNIX domain socket."),
    config_module: t.Optional[str] = typer.Option(
        None, help="Application Configuration Module"
    ),
    fd: t.Optional[int] = typer.Option(
        None, help="Bind to socket from this file descriptor."
    ),
    debug: bool = typer.Option(
        False, help="Enable debug mode.", is_flag=True, hidden=True
    ),
    reload: bool = typer.Option(False, help="Enable auto-reload.", is_flag=True),
    reload_dirs: t.List[Path] = typer.Option(
        [],
        "--reload-dir",
        help="Set reload directories explicitly, instead of using the current working directory.",
        exists=True,
    ),
    reload_includes: t.List[str] = typer.Option(
        [],
        "--reload-include",
        help="Set glob patterns to include while watching for files. Includes '*.py' "
        "by default; these defaults can be overridden with `--reload-exclude`. "
        "This option has no effect unless watchfiles is installed.",
        exists=True,
    ),
    reload_excludes: t.List[str] = typer.Option(
        [],
        "--reload-exclude",
        help="Set glob patterns to exclude while watching for files. Includes "
        "'.*, .py[cod], .sw.*, ~*' by default; these defaults can be overridden "
        "with `--reload-include`. This option has no effect unless watchfiles is "
        "installed.",
    ),
    reload_delay: float = typer.Option(
        0.25,
        show_default=True,
        help="Delay between previous and next check if application needs to be. Defaults to 0.25s.",
    ),
    workers: t.Optional[int] = typer.Option(
        None,
        show_default=True,
        help="Number of worker processes. Defaults to the $WEB_CONCURRENCY environment"
        " variable if available, or 1. Not valid with --reload.",
    ),
    loop: LOOP_CHOICES = typer.Option(
        LOOP_CHOICES.auto.value, show_default=True, help="Event loop implementation."
    ),
    http: HTTP_CHOICES = typer.Option(
        HTTP_CHOICES.auto.value, show_default=True, help="HTTP protocol implementation."
    ),
    ws: WS_CHOICES = typer.Option(
        WS_CHOICES.auto.value,
        show_default=True,
        help="WebSocket protocol implementation.",
    ),
    ws_max_size: int = typer.Option(
        16777216, show_default=True, help="WebSocket max size message in bytes"
    ),
    ws_ping_interval: float = typer.Option(
        20.0, show_default=True, help="WebSocket ping interval"
    ),
    ws_ping_timeout: float = typer.Option(
        20.0, show_default=True, help="WebSocket ping timeout"
    ),
    ws_per_message_deflate: bool = typer.Option(
        True, show_default=True, help="WebSocket per-message-deflate compression"
    ),
    lifespan: LIFESPAN_CHOICES = typer.Option(
        LIFESPAN_CHOICES.auto.value, show_default=True, help="Lifespan implementation."
    ),
    interface: INTERFACE_CHOICES = typer.Option(
        INTERFACE_CHOICES.auto.value,
        show_default=True,
        help="Select ASGI3, ASGI2, or WSGI as the application interface.",
    ),
    env_file: t.Optional[Path] = typer.Option(
        None, show_default=True, exists=True, help="Environment configuration file."
    ),
    log_level: t.Optional[LOG_LEVELS] = typer.Option(
        None,
        show_default=True,
        help="Log level. [default: None]",
    ),
    access_log: bool = typer.Option(
        True,
        "--access-log/--no-access-log",
        is_flag=True,
        help="Enable/Disable access log.",
    ),
    use_colors: t.Optional[bool] = typer.Option(
        None,
        "--use-colors/--no-use-colors",
        is_flag=True,
        help="Enable/Disable colorized logging.",
    ),
    proxy_headers: bool = typer.Option(
        True,
        "--proxy-headers/--no-proxy-headers",
        is_flag=True,
        help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port to "
        "populate remote address info.",
    ),
    server_header: bool = typer.Option(
        True,
        "--server-header/--no-server-header",
        is_flag=True,
        help="Enable/Disable default Server header.",
    ),
    date_header: bool = typer.Option(
        True,
        "--date-header/--no-date-header",
        is_flag=True,
        help="Enable/Disable default Date header.",
    ),
    forwarded_allow_ips: t.Optional[str] = typer.Option(
        None,
        help="Comma separated list of IPs to trust with proxy headers. Defaults to"
        " the $FORWARDED_ALLOW_IPS environment variable if available, or '127.0.0.1'.",
    ),
    root_path: str = typer.Option(
        "",
        help="Set the ASGI '--root-path' for applications sub-mounted below a given URL path.",
    ),
    limit_concurrency: t.Optional[int] = typer.Option(
        None,
        help="Maximum number of concurrent connections or tasks to allow, before issuing"
        " HTTP 503 responses.",
    ),
    backlog: int = typer.Option(
        2048,
        help="Maximum number of connections to hold in backlog",
    ),
    limit_max_requests: t.Optional[int] = typer.Option(
        None,
        help="Maximum number of requests to service before terminating the process.",
    ),
    timeout_keep_alive: int = typer.Option(
        5,
        help="Close Keep-Alive connections if no new data is received within this timeout.",
        show_default=True,
    ),
    ssl_keyfile: t.Optional[str] = typer.Option(
        None,
        help="SSL key file",
        show_default=True,
    ),
    ssl_certfile: t.Optional[str] = typer.Option(
        None,
        help="SSL certificate file",
        show_default=True,
    ),
    ssl_keyfile_password: t.Optional[str] = typer.Option(
        None,
        help="SSL keyfile password",
        show_default=True,
    ),
    ssl_version: int = typer.Option(
        int(SSL_PROTOCOL_VERSION),
        help="SSL version to use (see stdlib ssl module's)",
        show_default=True,
    ),
    ssl_cert_reqs: int = typer.Option(
        int(ssl.CERT_NONE),
        help="Whether client certificate is required (see stdlib ssl module's)",
        show_default=True,
    ),
    ssl_ca_certs: t.Optional[str] = typer.Option(
        None,
        help="CA certificates file",
        show_default=True,
    ),
    ssl_ciphers: str = typer.Option(
        "TLSv1",
        help="Ciphers to use (see stdlib ssl module's)",
        show_default=True,
    ),
    headers: t.List[str] = typer.Option(
        [],
        "--header",
        help="Specify custom default HTTP response headers as a Name:Value pair",
    ),
    app_dir: str = typer.Option(
        default=".",
        show_default=True,
        help="Look for APP in the specified directory, by adding this to the PYTHONPATH."
        " Defaults to the current working directory.",
    ),
    h11_max_incomplete_event_size: int = typer.Option(
        default=DEFAULT_MAX_INCOMPLETE_EVENT_SIZE,
        help="For h11, the maximum number of bytes to buffer of an incomplete event.",
    ),
    factory: bool = typer.Option(
        is_flag=True,
        default=False,
        help="Treat APP as an application factory, i.e. a () -> <ASGI app> callable.",
        show_default=True,
    ),
):
    """- Starts Uvicorn Server -"""
    ellar_project_meta = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))

    if not ellar_project_meta:
        raise EllarCLIException("No pyproject.toml file found.")

    if not ellar_project_meta.has_meta:
        raise EllarCLIException(
            "No available project found. please create ellar project with `ellar create-project 'project-name'`"
        )

    _possible_config_module = ellar_project_meta.project_meta.config
    application = None if factory else ellar_project_meta.project_meta.application

    config_module_global = (
        os.environ.get(ELLAR_CONFIG_MODULE) or _possible_config_module
    )
    config = Config(config_module=config_module or config_module_global)

    log_config = config.LOGGING_CONFIG
    _log_level = config.LOG_LEVEL

    _log_level = log_level if log_level else _log_level or LOG_LEVELS.info

    init_kwargs = dict(
        host=host,
        port=port,
        uds=uds,
        fd=fd,
        loop=loop.value,
        http=http.value,
        ws=ws.value,
        ws_max_size=ws_max_size,
        ws_ping_interval=ws_ping_interval,
        ws_ping_timeout=ws_ping_timeout,
        lifespan=lifespan.value,
        env_file=env_file,
        log_config=LOGGING_CONFIG if log_config is None else log_config,
        log_level=_log_level.name,
        access_log=access_log,
        interface=interface.value,
        debug=debug,
        reload=reload,
        reload_dirs=reload_dirs or None,
        reload_includes=reload_includes or None,
        reload_excludes=reload_excludes or None,
        reload_delay=reload_delay,
        workers=workers,
        proxy_headers=proxy_headers,
        server_header=server_header,
        date_header=date_header,
        forwarded_allow_ips=forwarded_allow_ips,
        root_path=root_path,
        limit_concurrency=limit_concurrency,
        backlog=backlog,
        limit_max_requests=limit_max_requests,
        timeout_keep_alive=timeout_keep_alive,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        ssl_keyfile_password=ssl_keyfile_password,
        ssl_version=ssl_version,
        ssl_cert_reqs=ssl_cert_reqs,
        ssl_ca_certs=ssl_ca_certs,
        ssl_ciphers=ssl_ciphers,
        headers=[header.split(":", 1) for header in headers],
        use_colors=use_colors,
        factory=factory,
        app_dir=app_dir,
    )
    if sys.version_info >= (3, 7):
        init_kwargs.update(
            h11_max_incomplete_event_size=h11_max_incomplete_event_size,
            ws_per_message_deflate=ws_per_message_deflate,
        )

    uvicorn_run(application, **init_kwargs)
