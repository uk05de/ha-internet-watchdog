"""Constants for Internet Watchdog integration."""

DOMAIN = "internet_watchdog"

CONF_FRITZBOX_IP = "fritzbox_ip"
CONF_SWITCH_ENTITY = "switch_entity"
CONF_CHECK_INTERVAL = "check_interval"
CONF_FAILURE_THRESHOLD = "failure_threshold"
CONF_COOLDOWN = "cooldown"
CONF_MAX_RESTARTS = "max_restarts"
CONF_RETRY_PAUSE = "retry_pause"

DEFAULT_FRITZBOX_IP = "192.168.178.1"
DEFAULT_CHECK_INTERVAL = 60
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_COOLDOWN = 300
DEFAULT_MAX_RESTARTS = 3
DEFAULT_RETRY_PAUSE = 3600

# Hardcoded internet check targets (TCP connection to DNS servers)
INTERNET_CHECK_TARGETS = [
    ("8.8.8.8", 53),
    ("1.1.1.1", 53),
]
