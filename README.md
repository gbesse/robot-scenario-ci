# Robot Scenario CI

## Français

Alpha locale pour exécuter un **scénario robotique reproductible** et vérifier une trace d’événements JSONL. Le fichier de scénario fournit une commande, un délai maximal et les événements attendus. Le lanceur crée un emplacement temporaire `{telemetry}` à transmettre au processus, puis vérifie le résultat. L’exemple fourni est un faux robot déterministe ; il teste le lanceur, pas Gazebo.

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests
.venv/bin/robot-scenario-ci fixtures/obstacle.json --locale=fr
```

Pour Gazebo/Nav2, remplacer la commande de l’exemple par un lanceur local qui écrit les événements observés dans `{telemetry}` : `goal_sent`, `obstacle_detected`, `robot_stopped`, `route_replanned`, `goal_reached`. Adapter les assertions et fixer les versions du simulateur et du robot dans votre environnement CI. Le rapport ne prouve pas la sûreté réelle ni la fidélité de la simulation. La commande du scénario est exécutée telle quelle : n’utiliser que des scénarios de confiance. Codes de sortie : 0 succès, 1 échec du scénario, 2 entrée invalide.

### Reset Ledger

`robot-reset-ledger` vérifie qu’un épisode a exactement un début, une remise à zéro et une fin. Il compare les identifiants d’état initial, graines et versions entre deux essais, sans exiger le même résultat de tâche.

```sh
.venv/bin/robot-reset-ledger inspect fixtures/reset-run-a.jsonl --locale=fr
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-b.jsonl --locale=fr
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-drift.jsonl --locale=fr
```

La classe `ResetLedger` peut envelopper `env.reset()` ; elle intercepte aussi les appels à `self.reset()` effectués dans `step()`. Appeler `install()`, puis `begin_episode(id)` avant chaque remise à zéro, `end_episode(outcome)` après l’épisode, et `restore()` à la fin. Fournir une fonction `fingerprint(result)` qui renvoie un identifiant stable de l’état initial, ainsi que les versions exactes de l’environnement et du simulateur. Le contrôle ne prouve pas que deux états physiques réels sont identiques.

## English

Local alpha for running a **reproducible robot scenario** and checking a JSONL event trace. The scenario file supplies a command, timeout and expected events. The runner creates a temporary `{telemetry}` path for the process, then checks the outcome. The bundled example is a deterministic fake robot; it tests the runner, not Gazebo.

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests
.venv/bin/robot-scenario-ci fixtures/obstacle.json --locale=en
```

For Gazebo/Nav2, replace the sample command with a local launcher that writes observed events to `{telemetry}`: `goal_sent`, `obstacle_detected`, `robot_stopped`, `route_replanned`, `goal_reached`. Adapt assertions and pin simulator and robot versions in your CI environment. The report does not prove real-world safety or simulation fidelity. Scenario commands run as provided; use trusted scenarios only. Exit codes: 0 success, 1 scenario failure, 2 invalid input.

### Reset Ledger

`robot-reset-ledger` checks that each episode has exactly one begin, reset and end. It compares initial-state IDs, seeds and versions across two runs without requiring the same task outcome.

```sh
.venv/bin/robot-reset-ledger inspect fixtures/reset-run-a.jsonl --locale=en
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-b.jsonl --locale=en
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-drift.jsonl --locale=en
```

The `ResetLedger` class can wrap `env.reset()`; it also intercepts `self.reset()` calls made inside `step()`. Call `install()`, then `begin_episode(id)` before each reset, `end_episode(outcome)` after the episode, and `restore()` at the end. Provide a `fingerprint(result)` function that returns a stable initial-state ID, plus exact environment and simulator versions. This check does not prove two physical starting states are identical.

## Español

Alfa local para ejecutar un **escenario robótico reproducible** y comprobar un registro JSONL de eventos. El archivo del escenario aporta un comando, un tiempo límite y los eventos esperados. El ejecutor crea una ruta temporal `{telemetry}` para el proceso y comprueba el resultado. El ejemplo incluido es un robot simulado determinista; prueba el ejecutor, no Gazebo.

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests
.venv/bin/robot-scenario-ci fixtures/obstacle.json --locale=es
```

Para Gazebo/Nav2, sustituye el comando de ejemplo por un lanzador local que escriba los eventos observados en `{telemetry}`: `goal_sent`, `obstacle_detected`, `robot_stopped`, `route_replanned`, `goal_reached`. Ajusta las comprobaciones y fija las versiones del simulador y del robot en CI. El informe no demuestra seguridad real ni fidelidad de simulación. El comando del escenario se ejecuta tal como se proporciona: usa solo escenarios de confianza. Códigos de salida: 0 éxito, 1 fallo del escenario, 2 entrada no válida.

### Reset Ledger

`robot-reset-ledger` comprueba que cada episodio tenga exactamente un inicio, reinicio y fin. Compara identificadores de estado inicial, semillas y versiones entre dos pruebas sin exigir el mismo resultado de la tarea.

```sh
.venv/bin/robot-reset-ledger inspect fixtures/reset-run-a.jsonl --locale=es
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-b.jsonl --locale=es
.venv/bin/robot-reset-ledger compare fixtures/reset-run-a.jsonl fixtures/reset-run-drift.jsonl --locale=es
```

La clase `ResetLedger` puede envolver `env.reset()`; también intercepta las llamadas a `self.reset()` realizadas dentro de `step()`. Ejecuta `install()`, después `begin_episode(id)` antes de cada reinicio, `end_episode(outcome)` tras el episodio y `restore()` al terminar. Proporciona una función `fingerprint(result)` que devuelva un identificador estable del estado inicial y las versiones exactas del entorno y del simulador. Esta comprobación no demuestra que dos estados físicos iniciales sean idénticos.

MIT — [LICENSE](LICENSE).
