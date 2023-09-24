import logging

log = logging.getLogger("ellar.di")
log.addHandler(logging.NullHandler())

if log.level == logging.NOTSET:
    log.setLevel(logging.WARN)
