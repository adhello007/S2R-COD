# AN-01 exploratory regression (EXPLORATORY / POST HOC; covariates are post-treatment; not causal)

## COD10K, boundary_f

| term | coef | 95% CI | p |
|---|---|---|---|
| Intercept | +0.39756 | [+0.35483, +0.44030] | 0.000 |
| C(arch)[T.SINetv2] | +0.01716 | [+0.01235, +0.02197] | 0.000 |
| concentrated | +0.00867 | [+0.00254, +0.01480] | 0.006 |
| n_appended | +0.00000 | [-0.00002, +0.00002] | 0.924 |
| jaccard_to_C10 | -0.00562 | [-0.01373, +0.00249] | 0.175 |
warnings: Maximum Likelihood optimization failed to converge. Check mle_retvals; Retrying MixedLM optimization with lbfgs; Maximum Likelihood optimization failed to converge. Check mle_retvals; Retrying MixedLM optimization with cg; Maximum Likelihood optimization failed to converge. Check mle_retvals; MixedLM optimization failed, trying a different optimizer may help.; Gradient optimization failed, |grad| = 0.518899; The MLE may be on the boundary of the parameter space.

## COD10K, boundary_iou

| term | coef | 95% CI | p |
|---|---|---|---|
| Intercept | +0.33568 | [+0.30458, +0.36678] | 0.000 |
| C(arch)[T.SINetv2] | -0.00588 | [-0.00938, -0.00237] | 0.001 |
| concentrated | +0.00636 | [+0.00190, +0.01083] | 0.005 |
| n_appended | -0.00000 | [-0.00002, +0.00001] | 0.760 |
| jaccard_to_C10 | -0.00469 | [-0.01060, +0.00122] | 0.120 |
warnings: Random effects covariance is singular; The MLE may be on the boundary of the parameter space.

## NC4K, boundary_f

| term | coef | 95% CI | p |
|---|---|---|---|
| Intercept | +0.45440 | [+0.42271, +0.48608] | 0.000 |
| C(arch)[T.SINetv2] | +0.01199 | [+0.00842, +0.01556] | 0.000 |
| concentrated | +0.00657 | [+0.00202, +0.01112] | 0.005 |
| n_appended | +0.00001 | [-0.00001, +0.00002] | 0.324 |
| jaccard_to_C10 | -0.00483 | [-0.01085, +0.00118] | 0.115 |
warnings: Random effects covariance is singular; The MLE may be on the boundary of the parameter space.

## NC4K, boundary_iou

| term | coef | 95% CI | p |
|---|---|---|---|
| Intercept | +0.36998 | [+0.34523, +0.39474] | 0.000 |
| C(arch)[T.SINetv2] | -0.00402 | [-0.00681, -0.00123] | 0.005 |
| concentrated | +0.00533 | [+0.00177, +0.00888] | 0.003 |
| n_appended | +0.00001 | [-0.00001, +0.00002] | 0.330 |
| jaccard_to_C10 | -0.00448 | [-0.00918, +0.00022] | 0.062 |
warnings: Random effects covariance is singular; The MLE may be on the boundary of the parameter space.

