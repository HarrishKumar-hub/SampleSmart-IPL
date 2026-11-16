# Section 1: Introduction, Population Definition & Sampling Frame Construction
**Author / Lead:** Member 1  
**Project:** Design, Estimation and Efficiency Comparison of Sampling Techniques on IPL Batting Data (2008–2024)

---

## 1.1 Project Overview & Research Objectives
This project presents an empirical and theoretical investigation into five fundamental sampling designs applied to a genuine, complete sports data population: the Indian Premier League (IPL) batting records spanning 2008 through 2024. 

The core research questions addressed are:
1. How do Simple Random Sampling (with and without replacement), Stratified Sampling (proportional and Neyman optimal allocations), Systematic Sampling, and Single-Stage Cluster Sampling perform when estimating population mean runs, population total runs, and the proportion of high-scoring innings (>= 30 runs)?
2. To what extent does domain-specific stratification (by batting order position) increase precision over unstratified sampling?
3. How does periodicity in the systematic sampling frame affect the sampling variance when the sampling interval k aligns with the natural team innings size?
4. What is the impact of match-level clustering (intra-cluster correlation rho) on estimation efficiency?

---

## 1.2 Target Population & Unit of Analysis
The population unit is defined as **one batter-innings**—specifically, a batter who faced at least one legal-record ball in innings 1 or 2 of an IPL match.
- **Deliveries considered:** Innings 1 and 2 only. Super-over deliveries (innings 3 through 6) were excluded as they represent artificial tie-break environments with vastly altered run-scoring mechanics (161 deliveries dropped).
- **Target Population Size (N):** Exactly **16,515** batter-innings across **1,095** matches.

### True Population Parameters (The Ground Truth)
Because the entire population is known from official Cricsheet records, we have exact benchmarks to evaluate sampling accuracy:
- **True Population Mean (mu):** **19.9696 runs**
- **True Population Standard Deviation (sigma):** **21.3509 runs** (Sample SD S = 21.3516)
- **True Population Total (tau):** **329,798 runs**
- **True Population Proportion of Innings >= 30 Runs (P):** **0.2488** (24.88%)

---

## 1.3 Data Cleaning & Canonicalisation Protocol
Raw data derived from Kaggle/Cricsheet underwent rigorous canonicalisation:
1. **Franchise Normalisation:** Historical rebrandings were harmonised to current identities (e.g. Delhi Daredevils -> Delhi Capitals, Kings XI Punjab -> Punjab Kings, Royal Challengers Bangalore -> Royal Challengers Bengaluru).
2. **Season Harmonisation:** Multi-year season labels were unified (e.g. 2007/08 -> 2008, 2009/10 -> 2010, 2020/21 -> 2021).
3. **Venue Canonicalisation:** 44 distinct stadium identities were resolved by removing city suffixes and formatting inconsistencies.
4. **Batting Position Derivation:** Batting position (1 to 11) was dynamically reconstructed chronologically from ball-by-ball delivery sequences as the order of appearance as striker or non-striker.

---

## 1.4 Data Quality Audit Log
| Metric / Check | Value | Verification Status |
|:---|:---:|:---:|
| Raw Deliveries Ingested | 260,920 | Verified |
| Raw Matches Ingested | 1,095 | Verified |
| Super-over deliveries dropped | 161 | Checked |
| Cleaned Sampling Frame Units (N) | **16,515** | Exact match |
| Missing Batting Positions | 0 | Passed (0 missing) |
| Missing Runs | 0 | Passed (0 missing) |
| Duplicate Records | 0 | Passed (0 duplicates) |
| Batters with 0 balls faced | 0 | Passed (0 zero-ball units) |
| Total Match Clusters | 1,095 | Verified |
| Mean Cluster Size | 15.08 batters/match | Verified (range 5-22) |
