# Interview walkthrough

1. Open the data ledger. Explain the different grains of spend and outcomes and
   why a naive join can over-count conversions.
2. Show `adstock` and explain how carryover survives the training/holdout boundary.
3. Explain the response features, coefficient bounds and regularisation. The
   decay rate is assumed, and the fixture matches the model family.
4. Run the holdout evaluation. Explain why observed future spend is permissible
   for this conditional task and why it would not be an unconditional forecast.
5. Run the leakage test that modifies holdout outcomes. Predictions must stay fixed.
6. Use the interface to change the total budget and movement cap. Reconcile every
   allocation to the total and explain the feasible bounds.
7. Explain why a 1.60% modelled scenario change is not causal or measured uplift.
8. Discuss what real-world validation, uncertainty estimation and operational
   controls would be required before a business used the recommendations.

Development was AI-assisted. Be prepared to explain, modify and rerun the actual
code, rather than treating generated code or synthetic metrics as work experience.
