# Section 7: Contextualisation with Official Statistics (NSO/MoSPI) & Project Conclusions
**Author / Lead:** Member 4  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 7.1 Contextualisation with National Statistical Systems
The theoretical tradeoffs demonstrated in this mini-project directly mirror the practical architectures deployed by national statistical agencies, notably the **National Statistical Office (NSO)** under the **Ministry of Statistics and Programme Implementation (MoSPI)**, Government of India.

### Parallels with the National Sample Survey (NSS):
1. **Stratification vs. Operational Feasibility:**
   - In NSS socioeconomic surveys (e.g. Periodic Labour Force Survey - PLFS), MoSPI does not use unstratified simple random sampling. Rural and urban areas are stratified into first-stage strata (districts/sub-districts), mirroring our position-based strata where between-stratum variation is removed to boost precision.
2. **Cluster Sampling in the Field:**
   - MoSPI utilizes villages (in rural areas) and Urban Frame Survey (UFS) blocks as Primary Sampling Units (PSUs). Full household enumeration within selected blocks corresponds to cluster sampling.
   - Just as our match-level cluster sampling suffered an efficiency penalty (Deff = 1.15) due to positive intra-cluster correlation (rho = +0.0109), national surveys routinely accommodate design effects between 1.2 and 2.5. Agencies deliberately accept this loss of precision per unit because the operational savings in travel, listing, and field management far outweigh the variance inflation.
3. **Systematic Selection at the Secondary Stage:**
   - Within selected PSUs, MoSPI surveys typically select households using circular systematic sampling. As demonstrated in our Section 4, systematic sampling requires careful scrutiny of listing orders to avoid periodicity alignment with physical neighborhood clusters.

---

## 7.2 Summary of Methodological Findings
1. **Neyman Allocation is Superior:** When stratum variances differ significantly (S_1 = 26.24 for openers vs. S_4 = 7.89 for tailenders), Neyman optimal allocation provides substantial precision gains (RE = 1.4224), outperforming proportional allocation (RE = 1.3426).
2. **Periodicity is a Critical Operational Hazard:** In systematic sampling, selecting an interval k = 15 that matches the natural cycle of the data generates substantial variance inflation (RE = 0.8532). Frame orderings must always be audited for cyclical structures.
3. **Cluster Sampling Requires Design Effect Adjustments:** When units share common unobserved factors (such as pitch and weather within a match), standard errors must be scaled by sqrt(Deff) using appropriate ratio estimators.

---

## 7.3 Member Contributions & Sign-Off
- **Member 1:** Frame creation, data hygiene and canonicalisation, data quality audit log, SRSWOR & SRSWR derivations, sample size justification, Streamlit Tab 1, Section 1 & 2 authorship.
- **Member 2:** Stratification framework, proportional and Neyman allocation algorithms, rounding mechanics, stratified estimation, One-Way ANOVA across strata, Streamlit Tab 2, Section 3 authorship.
- **Member 3:** Systematic sampling implementation, successive differences variance formulation, exhaustive k-start enumeration, periodicity diagnosis, Streamlit Tab 3, Section 4 authorship, all project visualisations.
- **Member 4:** Single-stage cluster sampling, ratio estimators for unequal clusters, ANOVA mean squares and ICC estimation, cross-design comparative analysis, Monte Carlo simulation orchestration, MoSPI official statistics contextualisation, Streamlit Tab 4, Section 5, 6 & 7 authorship.
