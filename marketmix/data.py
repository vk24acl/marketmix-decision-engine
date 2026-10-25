"""Reproducible synthetic data, with spend and outcomes kept at separate grains."""
from pathlib import Path
import csv
import sqlite3
import numpy as np

CHANNELS = ('paid_search', 'paid_social', 'display', 'video', 'email', 'affiliate')
ALPHA = 0.35
SCALE = 1000.0


def adstock(spend, alpha=ALPHA, initial=None):
    values = np.asarray(spend, dtype=float)
    if values.ndim != 2 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Spend must be a finite, non-negative 2D array.')
    if not 0 <= alpha < 1:
        raise ValueError('Adstock decay must be in [0, 1).')
    state = np.zeros(values.shape[1]) if initial is None else np.asarray(initial, dtype=float).copy()
    if state.shape != (values.shape[1],) or not np.isfinite(state).all() or (state < 0).any():
        raise ValueError('Initial carryover must match the channels and be non-negative.')
    result = np.empty_like(values)
    for i, row in enumerate(values):
        state = row + alpha * state
        result[i] = state
    return result


def synthetic(seed=43121, weeks=130):
    if weeks < 80:
        raise ValueError('At least 80 weeks are needed for the seasonal holdout baseline.')
    rng = np.random.default_rng(seed)
    t = np.arange(weeks)
    base = np.array([4600, 3600, 2300, 3100, 950, 1700], dtype=float)
    spend = base * rng.lognormal(0, .28, size=(weeks, len(CHANNELS)))
    transformed = np.log1p(adstock(spend) / SCALE)
    response = transformed @ np.array([55, 39, 17, 27, 32, 22])
    outcome = 85 + .35*t + 18*np.sin(2*np.pi*t/52) + 8*np.cos(2*np.pi*t/52)
    outcome = outcome + response + rng.normal(0, 7, weeks)
    return spend.round(2), outcome.round(3)


def write_data(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    spend, outcome = synthetic()
    with (directory/'weekly_spend.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['week', 'channel', 'spend_gbp'])
        for i, row in enumerate(spend):
            writer.writerows((i, name, float(value)) for name, value in zip(CHANNELS, row))
    with (directory/'weekly_outcomes.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['week', 'conversions'])
        writer.writerows(enumerate(map(float, outcome)))
    return spend, outcome


def load_data(directory):
    directory = Path(directory)
    with (directory/'weekly_spend.csv').open() as f:
        records = list(csv.DictReader(f))
    with (directory/'weekly_outcomes.csv').open() as f:
        outcomes = list(csv.DictReader(f))
    weeks = [int(row['week']) for row in outcomes]
    if weeks != list(range(len(weeks))):
        raise ValueError('Outcome weeks must be unique, ordered and contiguous from zero.')
    spend = np.full((len(weeks), len(CHANNELS)), np.nan)
    seen = set()
    for row in records:
        week, name = int(row['week']), row['channel']
        if not 0 <= week < len(weeks) or name not in CHANNELS or (week, name) in seen:
            raise ValueError('Invalid or duplicate week/channel spend key.')
        seen.add((week, name))
        spend[week, CHANNELS.index(name)] = float(row['spend_gbp'])
    outcome = np.array([float(row['conversions']) for row in outcomes])
    if not np.isfinite(spend).all() or (spend < 0).any():
        raise ValueError('Every week needs one finite, non-negative spend value per channel.')
    if not np.isfinite(outcome).all() or (outcome < 0).any():
        raise ValueError('Outcomes must be finite and non-negative.')
    return spend, outcome


def database(spend, outcome):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE spend(week INTEGER, channel TEXT, spend_gbp REAL, PRIMARY KEY(week,channel))')
    db.execute('CREATE TABLE outcomes(week INTEGER PRIMARY KEY, conversions REAL)')
    db.executemany('INSERT INTO spend VALUES(?,?,?)',
                   ((i, c, float(v)) for i, row in enumerate(spend) for c, v in zip(CHANNELS, row)))
    db.executemany('INSERT INTO outcomes VALUES(?,?)', enumerate(map(float, outcome)))
    return db
