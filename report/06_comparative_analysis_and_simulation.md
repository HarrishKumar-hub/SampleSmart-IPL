# Section 6: Comprehensive Comparative Analysis & Monte Carlo Simulation
**Author / Lead:** Member 4  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 6.1 Unified Master Comparison Table
All five sampling designs (and both stratified variants) were evaluated under an identical common target sample size n = 1,101.

| Sampling Design | Achieved n | Estimated Mean | SE(Mean) | 95% Confidence Interval | Estimated Total | Prop >= 30 | SE(Prop) | Absolute Error | RE vs. SRS (Sample) | RE vs. SRS (Simulation) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **SRSWOR** | 1101 | 18.2770 | 0.5719 | [17.16, 19.40] | 301,845 | 0.2225 | 0.0121 | 1.6926 | **1.0000** | **1.0000** |
| **SRSWR** | 1101 | 19.3206 | 0.6283 | [18.09, 20.55] | 319,080 | 0.2352 | 0.0128 | 0.6490 | 0.8285 | 0.9939 |
| **Stratified (Prop.)** | 1101 | 20.4315 | 0.6044 | [19.25, 21.62] | 337,426 | 0.2460 | 0.0119 | 0.4619 | 0.8954 | **1.3426** |
| **Stratified (Neyman)** | 1101 | 20.3287 | 0.5461 | [19.26, 21.40] | 335,729 | 0.2526 | 0.0115 | **0.3591** | **1.0969** | **1.4224** |
| **Systematic (k=15)** | 1101 | 20.6576 | 0.6352 | [19.41, 21.90] | 341,160 | 0.2661 | 0.0129 | 0.6880 | 0.8107 | 0.8532 |
| **Cluster (Match)** | 1125 | 19.0507 | 0.5602 | [17.95, 20.15] | 321,480 | 0.2293 | 0.0108 | 0.9189 | 1.0422 | 0.9586 |

*True Reference Values:* Mean mu = 19.9696, Total tau = 329,798, Proportion >= 30 = 0.2488.

---

## 6.2 Monte Carlo Simulation Analysis (500 Replications)
To eliminate random draw artifacts, each sampling design was executed 500 times using independent seeded random number generators.

### Empirical Performance Summary:
| Design | Empirical Mean | Bias | Empirical SE | RMSE | 95% CI Coverage | Empirical RE vs SRS |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stratified (Neyman)** | 19.9978 | +0.0282 | **0.5349** | **0.5351** | **95.2%** | **1.4224** |
| **Stratified (Prop.)** | 19.9882 | +0.0186 | 0.5506 | 0.5504 | 95.4% | **1.3426** |
| **SRSWOR** | 19.9973 | +0.0277 | 0.6380 | 0.6379 | 95.8% | 1.0000 |
| **SRSWR** | 19.9823 | +0.0127 | 0.6399 | 0.6394 | 94.0% | 0.9939 |
| **Cluster (Match)** | 20.0160 | +0.0464 | 0.6516 | 0.6526 | 96.0% | 0.9586 |
| **Systematic (k=15)** | 19.9510 | -0.0186 | 0.6907 | 0.6903 | 94.0% | 0.8532 |

### Key Takeaways from Simulation:
1. **Unbiasedness:** All designs exhibit negligible bias (|Bias| < 0.05 runs on a scale of ~20), verifying the mathematical consistency of all implemented estimators.
2. **Efficiency Hierarchy:**
   Stratified (Neyman) > Stratified (Prop.) > SRSWOR > SRSWR ~ Cluster > Systematic
3. **Coverage Validity:** 95% confidence intervals achieved actual coverage rates between 94.0% and 96.0%, conforming to theoretical confidence bounds.

---

## 6.3 Hypothesis Testing & Design Variance F-Tests
To establish statistical significance when comparing design precisions:
- **Test:** Two-sample F-test comparing SRSWOR against Stratified Proportional variance.
- **H0:** Var(SRSWOR) = Var(Stratified-Prop)
- **F = 1.1169, p = 6.6959e-02**
- Across the 500 Monte Carlo replications, the variance reduction achieved by Neyman stratification is significant at p < 0.001.
