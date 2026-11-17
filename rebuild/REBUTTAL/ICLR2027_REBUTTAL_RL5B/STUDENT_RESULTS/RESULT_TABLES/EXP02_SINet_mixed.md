# EXP-02 mixed models (DESCRIPTIVE; decide nothing)

Source: `RESULT_TABLES/EXP02_SINet_long.csv`

## level only

```
          Mixed Linear Model Regression Results
==========================================================
Model:            MixedLM Dependent Variable: boundary_iou
No. Observations: 43      Method:             REML        
No. Groups:       19      Scale:              0.0000      
Min. group size:  1       Log-Likelihood:     123.4967    
Max. group size:  5       Converged:          Yes         
Mean group size:  2.3                                     
----------------------------------------------------------
               Coef.  Std.Err.    z    P>|z| [0.025 0.975]
----------------------------------------------------------
Intercept       0.333    0.002 153.273 0.000  0.329  0.337
C(level)[T.B]  -0.004    0.004  -0.976 0.329 -0.012  0.004
C(level)[T.L1] -0.003    0.004  -0.630 0.529 -0.011  0.005
C(level)[T.LH]  0.000    0.003   0.028 0.977 -0.005  0.005
seed Var        0.000                                     
==========================================================

```
warnings: The MLE may be on the boundary of the parameter space.; The Hessian matrix at the estimated parameter values is not positive definite.

## exploratory: + fill distance + pseudo-label count (post-treatment)

**Could not be fit: LinAlgError: Singular matrix.** Allocation-level covariates (fill distance) are constant within each allocation and collinear with the allocation grouping at 11 allocations.

