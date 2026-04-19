# Origin App MVP

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-2.17-0A0A0A?logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![Status](https://img.shields.io/badge/Status-MVP-2E7D32)](#overview)
[![Tests](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](.github/workflows/ci.yml)

Interactive Dash MVP for exploring time-shifted residential energy usage with a gamified student dashboard.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Results](#results)
- [Documentation](#documentation)
- [Development](#development)
- [License](#license)
- [AI Assistance and Last Updated](#ai-assistance-and-last-updated)

## Overview

This repository contains a portfolio-ready MVP of an energy timing dashboard built with Dash and Plotly. The app replays simulated smart plug data from a CSV file and presents:

- Live usage playback
- Green-hours versus busy-hours consumption
- Daily and weekly points
- Streak progress
- Weekly challenges
- A normalized dorm leaderboard

Scope is intentionally narrow. This project is a front-end MVP backed by generated CSV data, not a production backend or a real-time device integration.

## Installation

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Regenerate the demo dataset if needed

```bash
python -m scripts.generate_demo_data
```

## Usage

Run the dashboard locally:

```bash
python -m app
```

Then open `http://127.0.0.1:8040`.

Notes:

- The tracked file `data/smart_plug_stream.csv` is the default demo dataset.
- You only need to regenerate the CSV when you want a fresh replay window.
- The current MVP is optimized for desktop viewing.

## Project Structure

```text
origin_app_mvp/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── data_service.py
│   └── ui_components.py
├── assets/
│   └── style.css
├── data/
│   └── smart_plug_stream.csv
├── docs/
│   └── architecture.md
├── scripts/
│   └── generate_demo_data.py
├── tests/
│   └── test_data_service.py
├── .editorconfig
├── .gitattributes
├── .gitignore
├── requirements-dev.txt
├── requirements.txt
└── README.md
```

## Results

- Live demo: https://edb1b02f-3405-48b9-920e-8062b52a411b.plotly.app/
- Delivered MVP behavior:
  - Simulated live playback from smart plug data
  - Per-student leaderboard normalization
  - Streak and challenge mechanics tied to energy timing

## Documentation

- [Architecture Notes](docs/architecture.md)

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the basic quality checks:

```bash
python -m pytest
python -m compileall app scripts
```

The repository includes a lightweight GitHub Actions workflow that installs dependencies, regenerates demo data, runs tests, and performs a compile smoke check.

## License

No `LICENSE` file is currently included in this repository.

## AI Assistance and Last Updated

This repository was reorganized with AI-assisted editing for structure, documentation, and baseline quality checks. The README and project layout were aligned against the current source tree rather than projected future features.

Last updated: April 19, 2026.
