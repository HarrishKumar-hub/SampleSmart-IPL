# Section 2: Simple Random Sampling (SRSWOR vs. SRSWR) & Sample Size Determination
**Author / Lead:** Member 1  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 2.1 Sample Size Determination
To ensure rigorous comparison across all five designs, a single common sample size n = 1,101 was established using textbook sample size determination formulas.

### Theoretical Formulation (Cochran 1977, §4.7)
For estimating the population mean mu with allowable margin of error e at 95% confidence level (z = 1.96):
- n_0 = (z * S / e)^2
Applying the finite population correction (FPC):
- n = n_0 / (1 + n_0 / N)

### Calculation for IPL Batting Population
Given population standard deviation S = 21.3516 and population size N = 16,515:
- Setting desired margin e = 1.22 runs yields n_0 = 1,101.
- Achieved margin of error for the mean: **+-1.22 runs**.
- For proportion of innings with >= 30 runs (P = 0.2488): Achieved margin of error: **+-0.0247** (~ +-2.5%).
- Crucially, n = 1,101 is an exact integer divisor of N = 16,515 (16,515 / 1,101 = 15), enabling clean systematic sampling with k = 15.

---

## 2.2 Estimators & Formulas
### Simple Random Sampling Without Replacement (SRSWOR)
- **Mean Estimator:** y_bar = (1/n) sum y_i
- **Variance of the Mean:** V(y_bar) = (1 - n/N) * (s^2 / n), where FPC = 1 - n/N = 0.9333
- **Total Estimator:** tau_hat = N * y_bar with V(tau_hat) = N^2 * V(y_bar)
- **Proportion Estimator:** p_hat = (1/n) sum I(y_i >= 30) with V(p_hat) = (1 - n/N) * p_hat(1 - p_hat) / (n - 1)

### Simple Random Sampling With Replacement (SRSWR)
- **Variance of the Mean:** V(y_bar) = s^2 / n (no FPC factor)
- **Theoretical Variance Ratio:**
  V(y_bar_WOR) / V(y_bar_WR) = (N - n) / (N - 1) = 0.933390

---

## 2.3 Empirical Results
From a single seeded draw (n = 1,101):

| Estimator / Metric | SRSWOR | SRSWR | Theoretical Difference |
|:---|:---:|:---:|:---:|
| Estimated Mean | **18.2770** | **19.3206** | True mu = 19.9696 |
| Standard Error (SE) | **0.5719** | **0.6283** | SRSWOR is more precise |
| 95% Confidence Interval | [17.16, 19.40] | [18.09, 20.55] | Both cover true mean |
| Absolute Error | 1.6926 | 0.6490 | — |
| Estimated Proportion >= 30 | 0.2225 | 0.2352 | True P = 0.2488 |
| SE(Proportion) | 0.0121 | 0.0128 | — |
| Estimated Total | 301,845 | 319,080 | True tau = 329,798 |
| Relative Efficiency vs SRSWOR | **1.0000** | **0.8285** | SRSWOR yields 17.1% gain |
