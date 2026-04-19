# Architecture Notes

## Overview

This project is a self-contained Dash MVP that replays generated smart plug data from a CSV file. It is designed as a presentation-ready prototype rather than a production system.

## Runtime Flow

1. `python -m scripts.generate_demo_data` creates `data/smart_plug_stream.csv`.
2. `python -m app` loads the CSV at startup.
3. `app.data_service` computes energy windows, per-student aggregates, points, streaks, and leaderboard metrics.
4. `app.ui_components` renders the dashboard cards and leaderboard views.
5. A Dash interval advances the replay index to simulate live updates.

## Data Model

The demo dataset uses four columns:

- `ts`: ISO timestamp
- `dorm`: dorm or group label
- `members`: student count used for normalization
- `power_w`: aggregate power draw in watts

Derived metrics such as `delta_kwh`, window labels, daily summaries, streaks, and weekly leaderboard points are computed in memory.

## Repository Conventions

- Runtime application code lives in `app/`.
- Reproducible helper scripts live in `scripts/`.
- Reference documentation lives in `docs/`.
- Tests focus on deterministic data and scoring behavior rather than full browser automation.

## Current Limitations

- No backend, authentication, or persistent datastore
- No real smart plug integration
- Demo data is simulated, not streamed from devices
- UI behavior is validated primarily through smoke checks and data-layer tests
