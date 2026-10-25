# Methods and assumptions

## Data and grain

`weekly_spend.csv` has one record per week and channel. `weekly_outcomes.csv`
has one conversion outcome per week. Keeping the tables separate prevents a
six-fold duplication of outcomes when joining spend. Data generation is seeded;
there are 130 weeks and six channels. No real customer records are included.

## Response model

For channel j, adstock is `state[t,j] = spend[t,j] + 0.35 * state[t-1,j]`.
Media features are `log(1 + state/1000)`. Additional features are an intercept,
linear trend and annual sine/cosine terms. Fitting uses regularised least
squares with non-negative media coefficients. The intercept is not penalised.

Decay, scale and feature form are fixed assumptions, not inferred hyperparameters.
The generator uses the same broad structural family as the fitted model. Strong
fixture performance therefore says little about a misspecified real-world model.

## Evaluation

Fit on weeks 0–103 and evaluate on weeks 104–129. Holdout outcomes never enter
the fitted coefficients. Holdout adstock is initialised using the final training
state. The comparison uses the outcome from exactly 52 weeks earlier, which is
available before the holdout begins for this split.

The evaluation uses observed holdout spend. It is a conditional response
prediction, not a forecast that also predicts future spend. RMSE and MAE are
reported for the same outcome units and dates. A planning model is fitted to
all 130 weeks only after the holdout evaluation is complete.

## Allocation

The reference shares come from the last eight observed spend weeks. Shares are
scaled to the selected total weekly budget. The optimiser chooses one constant
weekly allocation over four future weeks, carrying forward the latest adstock.
Total spend must equal the requested budget; each channel stays within the
chosen percentage of its scaled reference allocation.

SLSQP minimises negative predicted conversions. A zero movement limit returns
the reference allocation. Failure to converge or reconcile the budget raises
an error rather than returning a purported recommendation. The same fitted
response model evaluates both reference and optimised allocations.

## Limits and next steps

This is not a causal marketing mix study. There are no experimental calibration
data, omitted-variable controls, parameter uncertainty intervals or real-world
identification claims. Synthetic channels have useful variation by construction.
In actual data, collinearity, pricing, promotions, seasonality and distribution
shifts can change the conclusions. A next iteration should add rolling-origin
evaluation, response sensitivity analysis, uncertainty-aware planning and a
reviewed external dataset.

## Local app

The standard-library server is for a local demo. It binds to 127.0.0.1,
requires JSON for POST requests, rejects cross-origin browser requests and
validates planning inputs. It is not a production web service.
