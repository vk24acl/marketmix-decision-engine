"""Non-negative media response coefficients with a chronological holdout."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import lsq_linear
from .data import ALPHA, SCALE, adstock


def features(spend, start_week=0, initial=None):
    state = adstock(spend, initial=initial)
    t = np.arange(start_week, start_week+len(state))
    return np.column_stack([np.ones(len(t)), t/52, np.sin(2*np.pi*t/52),
                            np.cos(2*np.pi*t/52), np.log1p(state/SCALE)])


@dataclass
class ResponseModel:
    coefficients: np.ndarray

    def predict(self, spend, start_week=0, initial=None):
        return features(spend, start_week, initial) @ self.coefficients


def fit(spend, outcome, penalty=.05):
    x = features(spend)
    y = np.asarray(outcome, dtype=float)
    if y.shape != (len(x),) or not np.isfinite(y).all() or len(y) < 20:
        raise ValueError('Supply at least 20 finite outcomes aligned with spend.')
    if not np.isfinite(penalty) or penalty < 0:
        raise ValueError('Penalty must be finite and non-negative.')
    regularizer = np.eye(x.shape[1]) * np.sqrt(penalty)
    regularizer[0, 0] = 0
    lower = np.r_[np.repeat(-np.inf, 4), np.zeros(x.shape[1]-4)]
    result = lsq_linear(np.vstack([x, regularizer]), np.r_[y, np.zeros(x.shape[1])],
                        bounds=(lower, np.repeat(np.inf, x.shape[1])), tol=1e-10)
    if not result.success:
        raise ValueError('Model fitting did not converge.')
    return ResponseModel(result.x)


def metrics(actual, predicted):
    error = np.asarray(actual)-np.asarray(predicted)
    return {'mae': float(np.mean(np.abs(error))), 'rmse': float(np.sqrt(np.mean(error**2)))}


def evaluate(spend, outcome, holdout=26):
    split = len(outcome)-holdout
    if holdout < 1 or split < 52 or holdout > 52:
        raise ValueError('Use a 1–52 week holdout with at least 52 training weeks.')
    # Only training outcomes reach fit. Future spend is an observed conditional input.
    model = fit(spend[:split], outcome[:split])
    carryover = adstock(spend[:split])[-1]
    predicted = model.predict(spend[split:], split, carryover)
    baseline = outcome[np.arange(split, len(outcome))-52]
    return {'training_weeks': split, 'holdout_weeks': holdout,
            'model': metrics(outcome[split:], predicted),
            'seasonal_naive': metrics(outcome[split:], baseline),
            'predictions': predicted.tolist(), 'actual': outcome[split:].tolist(),
            'baseline_predictions': baseline.tolist(),
            'evaluation_type': 'chronological holdout; observed future spend, not an unconditional forecast'}
