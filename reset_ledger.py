"""Record and compare simulator resets used in robot evaluations."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


MESSAGES = {
    "fr": {
        "missing": "Épisode {episode} absent d’un des essais",
        "sequence": "Épisode {episode} : ordre début → remise à zéro → fin non respecté",
        "reset_count": "Épisode {episode} : {count} remise(s) à zéro observée(s), une attendue",
        "begin_count": "Épisode {episode} : début absent ou répété",
        "end_count": "Épisode {episode} : fin absente ou répétée",
        "state": "Épisode {episode} : état initial différent",
        "seed": "Épisode {episode} : graine différente",
        "environment": "Épisode {episode} : version d’environnement différente",
        "simulator": "Épisode {episode} : version de simulateur différente",
        "input": "Journal invalide : {detail}",
        "summary": "{count} anomalie(s) sur {episodes} épisode(s)",
    },
    "en": {
        "missing": "Episode {episode} is missing from one run",
        "sequence": "Episode {episode}: begin → reset → end order was not followed",
        "reset_count": "Episode {episode}: observed {count} reset(s); expected one",
        "begin_count": "Episode {episode}: begin event missing or repeated",
        "end_count": "Episode {episode}: end event missing or repeated",
        "state": "Episode {episode}: different initial state",
        "seed": "Episode {episode}: different seed",
        "environment": "Episode {episode}: different environment revision",
        "simulator": "Episode {episode}: different simulator version",
        "input": "Invalid ledger: {detail}",
        "summary": "{count} finding(s) across {episodes} episode(s)",
    },
    "es": {
        "missing": "Falta el episodio {episode} en una de las pruebas",
        "sequence": "Episodio {episode}: no se siguió el orden inicio → reinicio → fin",
        "reset_count": "Episodio {episode}: se observaron {count} reinicio(s); se esperaba uno",
        "begin_count": "Episodio {episode}: inicio ausente o repetido",
        "end_count": "Episodio {episode}: fin ausente o repetido",
        "state": "Episodio {episode}: estado inicial distinto",
        "seed": "Episodio {episode}: semilla distinta",
        "environment": "Episodio {episode}: versión del entorno distinta",
        "simulator": "Episodio {episode}: versión del simulador distinta",
        "input": "Registro no válido: {detail}",
        "summary": "{count} anomalía(s) en {episodes} episodio(s)",
    },
}


class ResetLedger:
    """Instrument an environment whose step() may call self.reset() internally."""

    def __init__(self, environment, path, fingerprint, *, environment_revision, simulator_version):
        if not callable(fingerprint):
            raise ValueError("fingerprint must be callable")
        self.environment = environment
        self.path = Path(path)
        if self.path.exists():
            raise ValueError("ledger path already exists")
        self.fingerprint = fingerprint
        self.environment_revision = environment_revision
        self.simulator_version = simulator_version
        self.current_episode = None
        self.started_ns = time.monotonic_ns()
        self._original_reset = None
        self._had_instance_reset = False

    def _write(self, event, episode, **details):
        record = {"event": event, "episode": episode, "at_ms": (time.monotonic_ns() - self.started_ns) // 1_000_000, **details}
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    def install(self):
        if self._original_reset is not None:
            raise ValueError("already installed")
        self._had_instance_reset = "reset" in getattr(self.environment, "__dict__", {})
        self._original_reset = self.environment.reset

        def observed_reset(*args, **kwargs):
            result = self._original_reset(*args, **kwargs)
            self._write(
                "reset",
                self.current_episode or "_unassigned",
                state_id=str(self.fingerprint(result)),
                seed=kwargs.get("seed"),
                environment_revision=self.environment_revision,
                simulator_version=self.simulator_version,
            )
            return result

        self.environment.reset = observed_reset
        return self

    def restore(self):
        if self._original_reset is None:
            return
        if self._had_instance_reset:
            self.environment.reset = self._original_reset
        else:
            delattr(self.environment, "reset")
        self._original_reset = None

    def begin_episode(self, episode):
        if self.current_episode is not None or not isinstance(episode, str) or not episode:
            raise ValueError("episode already active or invalid")
        self.current_episode = episode
        self._write("begin", episode)

    def end_episode(self, outcome):
        if self.current_episode is None:
            raise ValueError("no active episode")
        self._write("end", self.current_episode, outcome=outcome)
        self.current_episode = None


def _finding(locale, code, episode, **details):
    return {"code": code, "episode": episode, "details": details, "message": MESSAGES[locale][code].format(episode=episode, **details)}


def _summarize(events, locale):
    if not events:
        raise ValueError("empty ledger")
    episodes = {}
    previous_ms = -1
    for line, event in enumerate(events, 1):
        if not isinstance(event, dict) or event.get("event") not in ("begin", "reset", "end") or not isinstance(event.get("episode"), str) or not event["episode"]:
            raise ValueError(f"line {line}: event/episode")
        stamp = event.get("at_ms")
        if not isinstance(stamp, int) or isinstance(stamp, bool) or stamp < previous_ms:
            raise ValueError(f"line {line}: at_ms")
        previous_ms = stamp
        episode = event["episode"]
        state = episodes.setdefault(episode, {"begin": 0, "end": 0, "resets": [], "sequence": []})
        state["sequence"].append(event["event"])
        if event["event"] == "reset":
            for field in ("state_id", "environment_revision", "simulator_version"):
                if not isinstance(event.get(field), str) or not event[field]:
                    raise ValueError(f"line {line}: {field}")
            state["resets"].append({key: event.get(key) for key in ("state_id", "seed", "environment_revision", "simulator_version")})
        else:
            state[event["event"]] += 1
    findings = []
    for episode, state in episodes.items():
        if state["begin"] != 1:
            findings.append(_finding(locale, "begin_count", episode))
        if state["end"] != 1:
            findings.append(_finding(locale, "end_count", episode))
        if len(state["resets"]) != 1:
            findings.append(_finding(locale, "reset_count", episode, count=len(state["resets"])))
        if state["sequence"] != ["begin", "reset", "end"]:
            findings.append(_finding(locale, "sequence", episode))
    return episodes, findings


def inspect(events, locale="en"):
    episodes, findings = _summarize(events, locale)
    return {
        "format": "robot-reset-ledger/v1",
        "locale": locale,
        "status": "pass" if not findings else "fail",
        "summary": MESSAGES[locale]["summary"].format(count=len(findings), episodes=len(episodes)),
        "episodes": episodes,
        "findings": findings,
    }


def compare(first, second, locale="en"):
    left, findings = _summarize(first, locale)
    right, right_findings = _summarize(second, locale)
    for finding in findings:
        finding["source"] = "first"
    for finding in right_findings:
        finding["source"] = "second"
    findings.extend(right_findings)
    for episode in sorted(set(left) | set(right)):
        if episode not in left or episode not in right:
            findings.append(_finding(locale, "missing", episode))
            continue
        if len(left[episode]["resets"]) != 1 or len(right[episode]["resets"]) != 1:
            continue
        first_reset = left[episode]["resets"][0]
        second_reset = right[episode]["resets"][0]
        for field, code in (("state_id", "state"), ("seed", "seed"), ("environment_revision", "environment"), ("simulator_version", "simulator")):
            if first_reset[field] != second_reset[field]:
                findings.append(_finding(locale, code, episode))
    return {
        "format": "robot-reset-ledger/v1",
        "locale": locale,
        "status": "pass" if not findings else "fail",
        "summary": MESSAGES[locale]["summary"].format(count=len(findings), episodes=len(set(left) | set(right))),
        "findings": findings,
    }


def _read(path):
    raw = Path(path).read_bytes()
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()], hashlib.sha256(raw).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect or compare simulator resets / Examiner les remises à zéro / Inspeccionar reinicios del simulador")
    parser.add_argument("action", choices=("inspect", "compare"))
    parser.add_argument("first")
    parser.add_argument("second", nargs="?")
    parser.add_argument("--locale", choices=MESSAGES, default="en")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        left, left_hash = _read(args.first)
        if args.action == "compare":
            if not args.second:
                raise ValueError("second ledger required")
            right, right_hash = _read(args.second)
            report = compare(left, right, args.locale)
            report["sources"] = [{"path": args.first, "sha256": left_hash}, {"path": args.second, "sha256": right_hash}]
        else:
            if args.second:
                raise ValueError("second ledger is only used with compare")
            report = inspect(left, args.locale)
            report["sources"] = [{"path": args.first, "sha256": left_hash}]
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        print(MESSAGES[args.locale]["input"].format(detail=exc), file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
