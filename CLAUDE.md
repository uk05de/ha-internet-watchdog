# Internet Watchdog — CLAUDE.md

## Project
- HA Custom Integration for monitoring internet/FritzBox connectivity
- Repo: uk05de/ha-internet-watchdog
- Auto-restarts FritzBox via Shelly switch when internet is down
- HACS compatible

## Architecture
- Custom HA integration with config flow (UI-based, no YAML)
- WatchdogCoordinator in __init__.py: central logic for checking + restarting
- Internet check: TCP connection to 8.8.8.8:53 and 1.1.1.1:53 (hardcoded, reliable)
- FritzBox check: HTTP HEAD to configurable FritzBox URL
- Restart: calls switch.turn_off on configured Shelly entity
- Shelly is configured to auto-turn-on after 10 seconds (power cycle)

## Hardware Setup
- FritzBox router (occasionally hangs, loses internet)
- Shelly switch in front of FritzBox power supply
- Shelly configured: always-on, auto-on after 10s when turned off
- HA on local network (still reachable when FritzBox hangs)

## Key Files
- custom_components/internet_watchdog/__init__.py — WatchdogCoordinator + setup
- custom_components/internet_watchdog/config_flow.py — Config + options flow
- custom_components/internet_watchdog/binary_sensor.py — Internet + FritzBox connectivity
- custom_components/internet_watchdog/sensor.py — Restart count + last restart timestamp
- custom_components/internet_watchdog/button.py — Manual restart button
- custom_components/internet_watchdog/switch.py — Auto-restart on/off toggle
- custom_components/internet_watchdog/const.py — Constants + defaults
- custom_components/internet_watchdog/strings.json — German UI strings
- custom_components/internet_watchdog/manifest.json — Integration metadata

## Entities
- Binary sensor: Internetverbindung (connectivity, on=connected)
- Binary sensor: FritzBox (connectivity, on=reachable) — only if FritzBox URL configured
- Sensor: Neustarts (counter, RestoreEntity)
- Sensor: Letzter Neustart (timestamp)
- Button: FritzBox Neustart (manual trigger)
- Switch: Automatischer Neustart (on/off, RestoreEntity, entity_category config)

## Config Flow
- Initial setup: FritzBox URL, Shelly switch entity, check interval, failure threshold, cooldown, max restarts
- Options flow: same fields, all changeable
- Only one instance allowed (unique_id based)

## Restart Logic
1. Every check_interval seconds: TCP connect to 8.8.8.8:53 + 1.1.1.1:53
2. If ANY succeeds → internet OK, reset failure counter
3. If ALL fail → increment consecutive_failures
4. After failure_threshold consecutive failures → trigger restart (switch.turn_off)
5. Enter cooldown (skip checks for cooldown seconds, FritzBox rebooting)
6. After cooldown → resume checks
7. If still failing → restart again (up to max_restarts times)
8. After max_restarts without recovery → stop auto-restarting, log warning
9. When internet recovers → reset all counters

## Defaults
- Check interval: 60s
- Failure threshold: 3 (= ~3 min detection time)
- Cooldown: 300s (5 min for FritzBox to boot)
- Max restarts: 3 (prevents infinite loop if ISP is down)

## Important Notes
- Version is in manifest.json
- Internet check uses TCP (no root/raw sockets needed, no DNS dependency)
- FritzBox check uses HTTP HEAD (ssl=False for local http://)
- Auto-restart switch state persists via RestoreEntity
- Restart count persists via RestoreEntity
- All entities share one device: "Internet Watchdog"
