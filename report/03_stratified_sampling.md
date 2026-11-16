# Section 3: Stratified Random Sampling (Proportional vs. Neyman Allocation)
**Author / Lead:** Member 2  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 3.1 Stratification Strategy
In Twenty20 cricket, a batter's scoring opportunity is heavily constrained by their position in the batting order. Openers face the powerplay overs with field restrictions, middle-order batters face spin and rebuilding phases, while tailenders face few balls with high risk.

The population was partitioned into **4 mutually exclusive strata** based on batting position:
1. **Openers (Positions 1–2):** N_1 = 4,365, Mean = 28.61, S_1 = 26.24
2. **Middle Order (Positions 3–5):** N_2 = 6,261, Mean = 23.07, S_2 = 20.84
3. **Lower-Middle Order (Positions 6–7):** N_3 = 3,200, Mean = 13.91, S_3 = 13.73
4. **Tail (Positions 8–11):** N_4 = 2,689, Mean = 5.92, S_4 = 7.89

The dramatic drop in stratum means (28.6 -> 23.1 -> 13.9 -> 5.9) provides a textbook foundation for variance reduction through stratification.

---

## 3.2 Allocation Methods & Mathematical Formulation
### 1. Proportional Allocation (Bowley)
Sample sizes are proportional to stratum sizes: n_h = n * (N_h / N)

### 2. Neyman Optimal Allocation
Sample sizes account for both stratum size and internal variability: n_h = n * (N_h * S_h) / sum(N_k * S_k)

### Stratum Allocations Comparison (n = 1,101)
| Stratum | N_h | Stratum Weight W_h | S_h | Proportional n_h | Neyman n_h | Difference |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Openers (1–2) | 4,365 | 0.2643 | 26.24 | 291 | **407** | +116 (Higher variance) |
| Middle (3–5) | 6,261 | 0.3791 | 20.84 | 418 | **463** | +45 |
| Lower-Middle (6–7) | 3,200 | 0.1938 | 13.73 | 213 | **156** | -57 |
| Tail (8–11) | 2,689 | 0.1628 | 7.89 | 179 | **75** | -104 (Lower variance) |
| **Total** | **16,515** | **1.0000** | — | **1101** | **1101** | Exact sum verified |

---

## 3.3 Estimation Results & Efficiency
### Stratified Estimators (Cochran 1977, Ch. 5)
- Combined Mean: y_bar_st = sum(W_h * y_bar_h)
- Variance: V(y_bar_st) = sum(W_h^2 * (1 - n_h/N_h) * s_h^2 / n_h)

### Empirical Performance
| Design | Estimate | SE | 95% CI | Variance | RE vs. SRSWOR |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Stratified Proportional** | 20.4315 | 0.6044 | [19.25, 21.62] | 0.365320 | **0.8954** |
| **Stratified Neyman** | 20.3287 | 0.5461 | [19.26, 21.40] | 0.298205 | **1.0969** |

In the 500-repetition Monte Carlo simulation, **Neyman allocation achieved an empirical Relative Efficiency of 1.4224** (a 42.2% reduction in variance relative to SRSWOR), and **Proportional allocation achieved an empirical RE of 1.3426**.

---

## 3.4 One-Way ANOVA across Batting Strata
To test whether stratum means are genuinely distinct:
- **H0:** mu_1 = mu_2 = mu_3 = mu_4 (stratum means are equal)
- **H1:** At least one stratum mean differs
- **Test Results:** F = 876.86, p = 0.0000e+00
- **Effect Size:** eta-squared = 0.1374 (13.74% of total variance explained by position)
- **Conclusion:** **Reject H0 decisively.** The highly significant F-statistic confirms that stratification by batting position successfully captures substantial between-stratum variation, directly driving the observed efficiency gains.
