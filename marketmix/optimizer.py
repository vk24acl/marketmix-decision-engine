"""Fixed-budget, bounded allocation using fitted diminishing-return responses."""
import numpy as np
from scipy.optimize import minimize
from .data import CHANNELS, adstock


def allocate(model, history, budget=None, movement=.30, horizon=4):
    history = np.asarray(history, dtype=float)
    adstock(history)  # Validate before using it as a planning state.
    if len(history) < 8:
        raise ValueError('Planning requires at least eight historical weeks.')
    base = history[-8:].mean(axis=0)
    if base.sum() <= 0:
        raise ValueError('Planning requires positive historical channel spend.')
    budget = float(base.sum()) if budget is None else float(budget)
    if not np.isfinite(budget) or budget <= 0 or budget > 1_000_000:
        raise ValueError('Weekly budget must be finite and between 0 and £1,000,000.')
    if not np.isfinite(movement) or not 0 <= movement <= .5:
        raise ValueError('Movement must be between 0 and 0.5.')
    if not isinstance(horizon, int) or not 1 <= horizon <= 12:
        raise ValueError('Planning horizon must be 1–12 weeks.')
    baseline = base/base.sum()*budget
    state = adstock(history)[-1]
    def expected(shares):
        future = np.tile(shares*budget, (horizon, 1))
        return float(model.predict(future, len(history), state).sum())
    shares = baseline/budget
    bounds = [(float(v*(1-movement)), float(v*(1+movement))) for v in shares]
    if movement == 0:
        chosen = shares
    else:
        result = minimize(lambda s: -expected(s), shares, method='SLSQP', bounds=bounds,
                          constraints=[{'type':'eq', 'fun':lambda s: s.sum()-1}],
                          options={'maxiter':500, 'ftol':1e-9})
        if not result.success:
            raise ValueError('Allocation did not converge: '+result.message)
        chosen = result.x
    assigned = chosen*budget
    if abs(assigned.sum()-budget) > .01 or not np.isfinite(assigned).all():
        raise ValueError('Allocation failed budget reconciliation.')
    before, after = expected(shares), expected(chosen)
    return {'weekly_budget':budget, 'allocated':float(assigned.sum()), 'horizon_weeks':horizon,
            'movement_limit':movement, 'baseline_expected':before, 'optimized_expected':after,
            'modelled_change_percent':float(100*(after/before-1)) if before else None,
            'channels':[{'channel':c, 'baseline_gbp':float(b), 'allocated_gbp':float(v),
                         'change_percent':float(100*(v/b-1))}
                        for c,b,v in zip(CHANNELS, baseline, assigned)],
            'interpretation':'Synthetic scenario estimates, not measured or causal business impact.'}
