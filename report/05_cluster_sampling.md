# Section 5: Single-Stage Cluster Sampling & Intra-Cluster Correlation (ICC)
**Author / Lead:** Member 4  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 5.1 Cluster Sampling Design
In sports administration and observational field audits, visiting random individual players across hundreds of matches is logistically prohibitive. Cluster sampling—where full matches are sampled and all players within selected matches are audited—represents the operational standard.

### Hierarchy & Unit Structure:
- **Primary Sampling Units (Clusters):** Full IPL Matches (M = 1,095 clusters in the population).
- **Secondary Units:** Batter-innings within each match.
- **Cluster Size Variability:** Cluster sizes m_i are unequal, ranging from 5 to 22 batters per match (mean cluster size M_bar = 15.08).
- **Sample Allocation:** To achieve an expected sample size of n ~ 1,101, m = 73 matches were drawn without replacement, yielding an actual sample size of n_actual = 1,125 batter-innings.

---

## 5.2 Ratio Estimator for Unequal Cluster Sizes
Because cluster sizes m_i vary, the sample mean cannot be calculated as a simple unweighted average of cluster means. Instead, we use Cochran's **Ratio Estimator** (Cochran 1977, §11.6):
y_bar_c = (sum y_i) / (sum m_i) = Total Runs in Sample Matches / Total Batters in Sample Matches

### Variance of the Ratio Estimator:
V_hat(y_bar_c) = ((1 - f_c) / (m * M_bar^2)) * (1 / (m - 1)) * sum (y_i - y_bar_c * m_i)^2
where f_c = m / M is the cluster sampling fraction.

### Unbiased Total Estimator:
tau_hat = (M / m) * sum y_i
with variance V_hat(tau_hat) = M^2 * ((1 - f_c) / m) * s_b^2, where s_b^2 = (1 / (m - 1)) * sum (y_i - y_bar_cluster)^2.

---

## 5.3 Empirical Results
From the drawn cluster sample (m = 73 matches, n_actual = 1,125):
- **Estimated Mean:** **19.0507 runs**
- **Standard Error:** **0.5602**
- **95% Confidence Interval:** **[17.95, 20.15]**
- **Unbiased Population Total:** **321,480 runs** (True: 329,798)

---

## 5.4 Intraclass Correlation Coefficient (ICC, rho) & Design Effect (Deff)
The efficiency of cluster sampling depends fundamentally on the degree of within-cluster homogeneity, quantified by the ICC (rho).

### ANOVA Formulation for Unequal Clusters (Cochran 1977, §11.10):
rho_hat = (MSB - MSW) / (MSB + (M_bar_0 - 1) * MSW)
where M_bar_0 = (1 / (M - 1)) * (N - sum(m_i^2) / N) = 15.08.

### Estimated Values:
- **Between-Match Mean Square (MSB):** 525.79
- **Within-Match Mean Square (MSW):** 450.93
- **ANOVA F-test:** F = 1.1660, p = 1.8388e-04
- **Intraclass Correlation (ICC, rho):** **+0.0109**
- **Design Effect (Deff):** **1.15**

### Contrast with Venue-Level Clusters:
When using stadiums (M = 44 venues) as clusters:
- **Venue ICC (rho):** **+0.0015**
- Because venues host matches across 17 years with differing pitch conditions and eras, within-venue correlation is lower than within-match correlation.

### Statistical Interpretation:
The positive ICC (rho = +0.0109) confirms that batters in the same match share common conditions (pitch pace, boundary size, match context, weather). Consequently, units within a cluster are slightly more homogeneous than random draws, producing a **Design Effect of 1.15**. This indicates that cluster sampling requires approximately 15% more sample units to attain the same precision as SRSWOR. In the 500-repetition simulation, Cluster Sampling exhibited an empirical RE of **0.9586**.
