# Section 4: Systematic Sampling & Periodicity Analysis
**Author / Lead:** Member 3  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 4.1 Systematic Frame Design
The frame was ordered logically by `(date, match_id, inning, batting_position)`.
Because N = 16,515 = 3^2 * 5 * 367, choosing k = 15 yields an exact integer sample size:
n = N / k = 16,515 / 15 = 1,101.
A 1-in-15 systematic sample is drawn by selecting a random starting integer r in {0, 1, ..., 14} and sampling units r, r+15, r+30, ..., r+(n-1)15.

---

## 4.2 Single-Sample Estimation & Variance Approximations
In practice, a systematic sample provides only one sample drawn from the population, making exact variance estimation from the sample impossible without modeling assumptions. We applied two primary formulations:

1. **Treat-as-SRS Approximation:**
   V_hat_SRS(y_bar_sys) = (1 - n/N) * (s^2 / n) = 0.403469 -> SE = 0.6352
2. **Successive Differences Estimator (Wolter 2007):**
   V_hat_SD(y_bar_sys) = (1 - n/N) / (2n(n-1)) * sum (y_(i+1) - y_i)^2

For starting point r = 0:
- Estimated Mean: **20.6576 runs**
- 95% Confidence Interval: **[19.41, 21.90]**
- Absolute Error: **0.6880**

---

## 4.3 Complete Enumeration across all k = 15 Starting Points
Because systematic sampling has exactly k = 15 possible samples in the entire sample space, we computed the **exact population sampling variance**:
V(y_bar_sys) = (1/k) sum (y_bar_r - mu)^2 = 0.487397
Comparing this to the analytic SRSWOR variance (V_SRS = 0.386464):
RE_exact = V(y_bar_SRS) / V(y_bar_sys) = 0.386464 / 0.487397 = **0.7929**

---

## 4.4 Diagnosis of Periodicity (The Hidden Trap of k = 15)
In standard survey sampling theory, systematic sampling on ordered lists usually improves precision over SRS when there is a monotonic trend. However, when the list exhibits **periodicity** and the sampling interval k coincides with the cycle length, systematic sampling is **less efficient** than SRS (Cochran 1977, §8.6).

### Why k = 15 Suffers from Periodicity:
In an IPL match, an innings typically sees 7 to 8 batters, meaning an entire match features approximately **15.08 batters**.
Because k = 15 almost perfectly matches the match cycle:
- A systematic sample starting at r = 0 or r = 1 repeatedly hits openers across multiple matches.
- A systematic sample starting at r = 10 repeatedly hits tailenders.
- This creates severe cluster-like homogeneity within each systematic sample and high between-sample variance.

### ANOVA across the k Systematic Samples
- **H0:** All 15 systematic sample means are identical
- **F = 1.2615, p = 0.2228**
- **Simulation Validation:** In the 500-repetition Monte Carlo simulation, systematic sampling exhibited an empirical RE of **0.8532**, confirming the loss of precision due to periodicity.
