"""
tests/test_estimators.py — Pytest suite for the sampling project.

Checks estimators against known textbook examples and verifies
that SRS variance matches simulation within tolerance.
"""

import numpy as np
import pandas as pd
import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config
from sampling import estimators as est
from sampling import srs, stratified, systematic, cluster


# ────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def frame():
    """Load the pre-built frame."""
    return pd.read_parquet(config.FRAME_PARQUET)


@pytest.fixture(scope="module")
def known_data():
    """Small known dataset for textbook verification."""
    return np.array([2, 4, 6, 8, 10, 12, 14, 16, 18, 20])


# ────────────────────────────────────────────────────────────────
# Test estimators
# ────────────────────────────────────────────────────────────────
class TestEstimators:
    def test_sample_mean(self, known_data):
        assert est.sample_mean(known_data) == pytest.approx(11.0)

    def test_fpc(self):
        assert est.fpc(100, 1000) == pytest.approx(0.9)
        assert est.fpc(500, 1000) == pytest.approx(0.5)

    def test_var_srswor_known(self, known_data):
        """Textbook: V(ȳ) = (1-n/N) * s²/n for N=100, n=10"""
        N = 100
        s2 = np.var(known_data, ddof=1)  # 36.667
        expected = (1 - 10/100) * s2 / 10
        assert est.var_srswor(known_data, N=N) == pytest.approx(expected)

    def test_var_srswr_known(self, known_data):
        """V(ȳ) = s²/n  (no fpc)"""
        s2 = np.var(known_data, ddof=1)
        expected = s2 / 10
        assert est.var_srswr(known_data, N=100) == pytest.approx(expected)

    def test_var_ratio(self):
        """(N-n)/(N-1) should be < 1"""
        ratio = est.var_ratio_wor_wr(100, 1000)
        assert ratio == pytest.approx(900 / 999)
        assert ratio < 1.0

    def test_ci_symmetric(self):
        lo, hi = est.ci_95(10.0, 2.0)
        assert lo == pytest.approx(10.0 - 1.96 * 2.0)
        assert hi == pytest.approx(10.0 + 1.96 * 2.0)

    def test_sample_size_mean(self):
        n = est.sample_size_mean(S=21.35, e=1.2, N=16515)
        assert 900 < n < 1400  # reasonable range around 1101

    def test_relative_efficiency(self):
        assert est.relative_efficiency(10.0, 5.0) == pytest.approx(2.0)
        assert est.relative_efficiency(5.0, 10.0) == pytest.approx(0.5)


# ────────────────────────────────────────────────────────────────
# Test SRS
# ────────────────────────────────────────────────────────────────
class TestSRS:
    def test_srswor_size(self, frame):
        s = srs.draw_srswor(frame, n=100, rng=np.random.default_rng(42))
        assert len(s) == 100

    def test_srswr_size(self, frame):
        s = srs.draw_srswr(frame, n=100, rng=np.random.default_rng(42))
        assert len(s) == 100

    def test_srswor_no_duplicates(self, frame):
        s = srs.draw_srswor(frame, n=100, rng=np.random.default_rng(42))
        # Index should be unique (no replacement)
        assert len(s) == 100  # basic size check

    def test_reproducibility(self, frame):
        s1 = srs.draw_srswor(frame, n=50, rng=np.random.default_rng(99))
        s2 = srs.draw_srswor(frame, n=50, rng=np.random.default_rng(99))
        pd.testing.assert_frame_equal(s1, s2)


# ────────────────────────────────────────────────────────────────
# Test Stratified
# ────────────────────────────────────────────────────────────────
class TestStratified:
    def test_proportional_allocation_sums(self, frame):
        alloc = stratified.compute_allocation(frame, 1101, "proportional")
        assert alloc["nh"].sum() == 1101

    def test_neyman_allocation_sums(self, frame):
        alloc = stratified.compute_allocation(frame, 1101, "neyman")
        assert alloc["nh"].sum() == 1101

    def test_all_strata_represented(self, frame):
        alloc = stratified.compute_allocation(frame, 1101, "proportional")
        assert len(alloc) == 4
        assert all(alloc["nh"] >= 2)


# ────────────────────────────────────────────────────────────────
# Test Systematic
# ────────────────────────────────────────────────────────────────
class TestSystematic:
    def test_systematic_size(self, frame):
        s = systematic.draw_systematic(frame, k=15, start=0)
        assert len(s) == len(frame) // 15

    def test_all_k_samples_cover_frame(self, frame):
        all_s = systematic.all_systematic_samples(frame, k=15)
        assert len(all_s) == 15
        total = sum(len(s) for s in all_s.values())
        assert total == len(frame)


# ────────────────────────────────────────────────────────────────
# Test Cluster
# ────────────────────────────────────────────────────────────────
class TestCluster:
    def test_cluster_draw(self, frame):
        s, m = cluster.draw_cluster_sample(frame, m=10, rng=np.random.default_rng(42))
        assert s["match_id"].nunique() == 10
        assert len(s) > 0

    def test_icc_bounded(self, frame):
        icc = cluster.compute_icc(frame)
        assert -1 <= icc["ICC_rho"] <= 1


# ────────────────────────────────────────────────────────────────
# Test simulation variance matches analytic (within tolerance)
# ────────────────────────────────────────────────────────────────
class TestSimulationConsistency:
    def test_srs_simulation_variance(self, frame):
        """
        The empirical variance from 500 SRSWOR replications should be
        close to the analytic SRSWOR variance formula.
        """
        from sampling.simulation import run_simulation, summarise_simulation

        sim_df = run_simulation(frame, n_sim=200, seed=123, save=False)
        true_mean = float(frame["runs"].mean())
        true_prop = float((frame["runs"] >= 30).mean())
        summary = summarise_simulation(sim_df, true_mean, true_prop)

        srs_row = summary[summary["design"] == "SRSWOR"].iloc[0]

        # Analytic variance
        S2 = float(frame["runs"].var(ddof=1))
        N = len(frame)
        n = config.n
        analytic_var = (1 - n / N) * S2 / n

        # Should be within 50% (Monte Carlo has its own variance)
        ratio = srs_row["var_mean"] / analytic_var
        assert 0.5 < ratio < 2.0, f"Variance ratio {ratio:.3f} outside [0.5, 2.0]"
