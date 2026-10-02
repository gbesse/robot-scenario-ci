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

## English

Local alpha for running a **reproducible robot scenario** and checking a JSONL event trace. The scenario file supplies a command, timeout and expected events. The runner creates a temporary `{telemetry}` path for the process, then checks the outcome. The bundled example is a deterministic fake robot; it tests the runner, not Gazebo.

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests
.venv/bin/robot-scenario-ci fixtures/obstacle.json --locale=en
```

For Gazebo/Nav2, replace the sample command with a local launcher that writes observed events to `{telemetry}`: `goal_sent`, `obstacle_detected`, `robot_stopped`, `route_replanned`, `goal_reached`. Adapt assertions and pin simulator and robot versions in your CI environment. The report does not prove real-world safety or simulation fidelity. Scenario commands run as provided; use trusted scenarios only. Exit codes: 0 success, 1 scenario failure, 2 invalid input.

## Español

Alfa local para ejecutar un **escenario robótico reproducible** y comprobar un registro JSONL de eventos. El archivo del escenario aporta un comando, un tiempo límite y los eventos esperados. El ejecutor crea una ruta temporal `{telemetry}` para el proceso y comprueba el resultado. El ejemplo incluido es un robot simulado determinista; prueba el ejecutor, no Gazebo.

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests
.venv/bin/robot-scenario-ci fixtures/obstacle.json --locale=es
```

Para Gazebo/Nav2, sustituye el comando de ejemplo por un lanzador local que escriba los eventos observados en `{telemetry}`: `goal_sent`, `obstacle_detected`, `robot_stopped`, `route_replanned`, `goal_reached`. Ajusta las comprobaciones y fija las versiones del simulador y del robot en CI. El informe no demuestra seguridad real ni fidelidad de simulación. El comando del escenario se ejecuta tal como se proporciona: usa solo escenarios de confianza. Códigos de salida: 0 éxito, 1 fallo del escenario, 2 entrada no válida.

MIT — [LICENSE](LICENSE).
