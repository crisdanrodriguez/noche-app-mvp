# Noche App MVP

A Dash prototype that replays simulated residential energy data to explore time-based usage incentives for students.

[![Tests](https://github.com/crisdanrodriguez/noche-app-mvp/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/crisdanrodriguez/noche-app-mvp/actions/workflows/tests.yml) [![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Dash 2.17.1](https://img.shields.io/badge/Dash-2.17.1-008DE4?logo=plotly&logoColor=white)](https://dash.plotly.com/) [![Last commit](https://img.shields.io/github/last-commit/crisdanrodriguez/noche-app-mvp/main)](https://github.com/crisdanrodriguez/noche-app-mvp/commits/main/)

**Created:** 2026-01-24 | **Last Updated:** 2026-04-19

## Overview

Noche App MVP is a local, single-user dashboard for examining how the timing of residential electricity use could affect a student-facing points system. It shows a selected demo dorm alongside other simulated dorms, with separate views of energy use during configured green and busy hours.

The application reads a generated smart-plug-style CSV and advances through its rows on a Dash timer. All energy, points, challenge, and leaderboard calculations happen in memory. The project is a presentation prototype; the repository does not contain device integration, authentication, a database, or evidence of measured energy savings.

## Key Features

- Timed replay of the bundled demo dataset, with a fixed demo location label and changing usage display.
- Per-student energy summaries for green hours (10:00–15:00) and busy hours (17:00–21:00).
- Daily and weekly points, streak progress, and four weekly challenges derived from the demo data.
- Weekly dorm leaderboard normalized by member count, with rank movement indicators.
- Script to generate a new seven-day simulated dataset.

## Tech Stack

- **Language:** Python; the CI workflow uses Python 3.11.
- **Application and visualization:** Dash 2.17.1, Dash Bootstrap Components 1.6.0, Plotly 5.22.0.
- **Data processing:** pandas 2.2.2 and CSV files.
- **Testing:** pytest 8.3.5 and GitHub Actions.

## Architecture

`scripts/generate_demo_data.py` produces rows with a timestamp, dorm name, member count, and power draw in watts. The tracked `data/smart_plug_stream.csv` allows the app to start without regenerating data. `app/data_service.py` loads the CSV, derives energy in kWh from successive readings, labels time windows, and calculates per-student metrics. `app/ui_components.py` renders the cards and leaderboard, while `app/app.py` owns the Dash layout and timer callbacks. See [architecture notes](docs/architecture.md) for the data flow and current limitations.

Green-hour usage earns more points than normal-hour usage; busy-hour usage subtracts points. Weekly challenge rewards are added per student after dorm energy points are divided by the member count. The streak display includes a configured **56-day demo baseline**, so it should not be interpreted as a streak observed in the seven-day dataset.

## Getting Started

### Prerequisites

- Python 3.11 and `pip` (the version used by CI).

### Install and run

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app
```

Open `http://127.0.0.1:8040` in a browser. The application uses the tracked CSV by default; no environment variables or external service credentials are required for local playback.

To install the test dependency and run the data-layer tests and compile check:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m compileall app scripts
```

## Usage

The dashboard replays the selected demo dorm automatically. Its cards show current simulated usage, points, streak progress, challenges, and the weekly leaderboard. To generate a new seven-day replay window, run the following command from the repository root **before starting or restarting** the app:

```bash
python -m scripts.generate_demo_data
```

This command overwrites the tracked `data/smart_plug_stream.csv` with simulated readings dated relative to the time it runs. The app loads the CSV at startup, so restart it after regeneration. The data is illustrative, not a record of physical smart plugs.

## Project Structure

```text
app/                 Dash entry point, configuration, scoring, and UI components
assets/style.css      Dashboard styles
data/                 Bundled simulated smart-plug CSV
docs/architecture.md Data flow and limitations
scripts/              Demo dataset generator
tests/                Data loading and scoring tests
.github/workflows/    Tests workflow
requirements*.txt     Runtime and development dependencies
```

## Demonstration

An existing [hosted demo](https://edb1b02f-3405-48b9-920e-8062b52a411b.plotly.app/) is linked from this repository. Its URL responded during this documentation update; the interactive behavior of that deployment was not independently checked. The local app and bundled CSV provide the reproducible demonstration path.

## Project Status

Experimental MVP. The repository provides a CSV-backed dashboard and focused data-layer tests. It does not include live device data, persistent storage, user accounts, or browser-level tests.
