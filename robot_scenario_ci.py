"""Run a robot scenario and assert on machine-readable outcome events."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


MESSAGES = {
    "fr": {
        "timeout": "Le scénario a dépassé {seconds} s",
        "exit": "La commande s’est terminée avec le code {code}",
        "missing": "Événement attendu absent : {event}",
        "sequence": "Événements attendus dans un ordre différent",
        "duration": "Durée {duration} ms supérieure à la limite {limit} ms",
        "stop": "Aucun arrêt après l’obstacle",
        "stop_late": "Arrêt {latency} ms après l’obstacle, limite {limit} ms",
        "input": "Scénario invalide : {detail}",
        "summary": "{count} anomalie(s) pour {name}",
    },
    "en": {
        "timeout": "Scenario exceeded {seconds} s",
        "exit": "Command exited with code {code}",
        "missing": "Expected event missing: {event}",
        "sequence": "Expected events occurred out of order",
        "duration": "Duration {duration} ms exceeds {limit} ms limit",
        "stop": "No stop event after obstacle",
        "stop_late": "Robot stopped {latency} ms after obstacle; limit {limit} ms",
        "input": "Invalid scenario: {detail}",
        "summary": "{count} finding(s) for {name}",
    },
    "es": {
        "timeout": "El escenario superó {seconds} s",
        "exit": "El comando terminó con el código {code}",
        "missing": "Falta el evento esperado: {event}",
        "sequence": "Los eventos esperados aparecen fuera de orden",
        "duration": "La duración {duration} ms supera el límite de {limit} ms",
        "stop": "No hubo parada tras el obstáculo",
        "stop_late": "El robot se detuvo {latency} ms tras el obstáculo; límite {limit} ms",
        "input": "Escenario no válido: {detail}",
        "summary": "{count} anomalía(s) para {name}",
    },
}


def evaluate(events, expected, locale="en"):
    if not isinstance(events, list) or not isinstance(expected, dict):
        raise ValueError("events must be a list and expect must be an object")
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("at_ms"), int) or not isinstance(event.get("event"), str):
            raise ValueError("each event needs integer at_ms and string event")
    findings = []

    def add(code, **details):
        findings.append({"code": code, "details": details, "message": MESSAGES[locale][code].format(**details)})

    kinds = [event["event"] for event in events]
    required_events = expected.get("events", [])
    for required in required_events:
        if required not in kinds:
            add("missing", event=required)
    if all(required in kinds for required in required_events):
        position = -1
        for required in required_events:
            try:
                position = kinds.index(required, position + 1)
            except ValueError:
                add("sequence")
                break
    if events and "max_duration_ms" in expected:
        duration = max(event["at_ms"] for event in events) - min(event["at_ms"] for event in events)
        if duration > expected["max_duration_ms"]:
            add("duration", duration=duration, limit=expected["max_duration_ms"])
    if expected.get("stop_after_obstacle"):
        obstacle_times = [event["at_ms"] for event in events if event["event"] == "obstacle_detected"]
        stop_times = [event["at_ms"] for event in events if event["event"] == "robot_stopped"]
        later = [stop - obstacle_times[0] for stop in stop_times if obstacle_times and stop >= obstacle_times[0]]
        if not obstacle_times or not later:
            add("stop")
        elif "max_stop_latency_ms" in expected and min(later) > expected["max_stop_latency_ms"]:
            add("stop_late", latency=min(later), limit=expected["max_stop_latency_ms"])
    return findings


def run(scenario, base, locale="en"):
    if not isinstance(scenario, dict) or not isinstance(scenario.get("name"), str):
        raise ValueError("name is required")
    command = scenario.get("command")
    timeout = scenario.get("timeout_s", 30)
    expected = scenario.get("expect")
    if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
        raise ValueError("command must be a nonempty string array")
    if sum("{telemetry}" in part for part in command) != 1:
        raise ValueError("command must contain exactly one {telemetry} placeholder")
    if not isinstance(timeout, (int, float)) or timeout <= 0 or not isinstance(expected, dict):
        raise ValueError("timeout_s must be positive and expect must be an object")
    if not isinstance(expected.get("events"), list) or not expected["events"]:
        raise ValueError("expect.events must be a nonempty list")
    if "max_stop_latency_ms" in expected and (not isinstance(expected["max_stop_latency_ms"], (int, float)) or expected["max_stop_latency_ms"] < 0):
        raise ValueError("max_stop_latency_ms must be nonnegative")
    findings = []

    def add(code, **details):
        findings.append({"code": code, "details": details, "message": MESSAGES[locale][code].format(**details)})

    with tempfile.TemporaryDirectory(prefix="robot-scenario-") as directory:
        telemetry = Path(directory) / "telemetry.jsonl"
        actual_command = [part.replace("{telemetry}", str(telemetry)) for part in command]
        try:
            result = subprocess.run(actual_command, cwd=base, timeout=timeout, capture_output=True, text=True, check=False)
            if result.returncode:
                add("exit", code=result.returncode)
        except subprocess.TimeoutExpired:
            add("timeout", seconds=timeout)
        events = []
        if telemetry.exists():
            events = [json.loads(line) for line in telemetry.read_text(encoding="utf-8").splitlines() if line.strip()]
        findings.extend(evaluate(events, expected, locale))
    return {
        "format": "robot-scenario-ci/v1",
        "name": scenario["name"],
        "locale": locale,
        "status": "pass" if not findings else "fail",
        "summary": MESSAGES[locale]["summary"].format(count=len(findings), name=scenario["name"]),
        "events": events,
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run and check a robot scenario / Exécuter un scénario robotique / Ejecutar un escenario robótico")
    parser.add_argument("scenario")
    parser.add_argument("--locale", choices=MESSAGES, default="en")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        path = Path(args.scenario).resolve()
        report = run(json.loads(path.read_text(encoding="utf-8")), path.parent, args.locale)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(MESSAGES[args.locale]["input"].format(detail=exc), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
