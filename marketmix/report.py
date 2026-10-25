"""One reproducible path shared by the CLI, API and checked-in example outputs."""
from pathlib import Path
import csv
import json
import numpy as np
from .data import CHANNELS, database, load_data, write_data
from .model import evaluate, fit
from .optimizer import allocate

ROOT = Path(__file__).resolve().parents[1]


def run(directory=None, budget=None, movement=.30):
    directory = Path(directory) if directory else ROOT/'data'
    if not (directory/'weekly_spend.csv').exists():
        write_data(directory)
    spend, outcome = load_data(directory)
    evaluation = evaluate(spend, outcome)
    planning_model = fit(spend, outcome)  # Refit only after the independent holdout evaluation.
    plan = allocate(planning_model, spend, budget, movement)
    with database(spend, outcome) as db:
        summary = [dict(zip(['channel','weeks','total_spend_gbp','mean_weekly_spend_gbp'],row))
                   for row in db.execute((ROOT/'sql/channel_summary.sql').read_text())]
    return {'data_type':'seeded synthetic data', 'seed':43121, 'weeks':len(outcome),
            'evaluation':evaluation, 'plan':plan, 'sql_channel_summary':summary,
            'media_coefficients':dict(zip(CHANNELS,map(float,planning_model.coefficients[4:]))) }


def save(report, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'evaluation.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    rows = report['plan']['channels']
    with (destination/'allocation.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
