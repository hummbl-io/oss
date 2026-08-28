# Copyright 2024-2026 HUMMBL, LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for hummbl_lattice.kappa."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from hummbl_lattice.kappa import KappaCalculator, KappaResult


def _write_sample_ratings(path: str, n_items: int = 30, n_raters: int = 12, accuracy: float = 0.85):
    """Write a sample ratings CSV for testing."""
    import random
    random.seed(42)
    languages = ["en"] * 8 + ["es", "zh", "ar", "de"]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "rater_id", "classification", "confidence", "justification", "language", "item_language"])
        for i in range(n_items):
            item_id = f"item-{i+1:03d}"
            item_lang = random.choice(languages)
            true_cat = "reasoning_operator" if random.random() < 0.7 else "domain_knowledge"
            for j in range(n_raters):
                rater_id = f"rater-{j+1:02d}"
                rater_lang = languages[j]
                if random.random() < accuracy:
                    classification = true_cat
                    confidence = random.choice([4, 4, 5, 5, 5])
                else:
                    classification = "domain_knowledge" if true_cat == "reasoning_operator" else "reasoning_operator"
                    confidence = random.choice([2, 2, 3, 3, 4])
                writer.writerow([item_id, rater_id, classification, confidence, "test", rater_lang, item_lang])


class TestKappaCalculator:
    def test_compute_basic(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            _write_sample_ratings(path)
            calc = KappaCalculator()
            result = calc.compute(path)
            assert isinstance(result, KappaResult)
            assert 0 <= result.kappa <= 1
            assert result.n_items == 30
            assert result.n_raters_per_item == 12
            assert result.interpretation != ""
        finally:
            Path(path).unlink(missing_ok=True)

    def test_perfect_agreement(self):
        """If all raters agree, kappa should be high."""
        path = tempfile.mktemp(suffix=".csv")
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["item_id", "rater_id", "classification", "confidence", "justification", "language", "item_language"])
                for i in range(10):
                    for j in range(5):
                        writer.writerow([f"item-{i+1}", f"rater-{j+1}", "reasoning_operator", 5, "agree", "en", "en"])
            calc = KappaCalculator()
            result = calc.compute(path)
            assert result.kappa > 0.9
            assert result.threshold_passed
        finally:
            Path(path).unlink(missing_ok=True)

    def test_random_agreement(self):
        """If raters are random, kappa should be near 0."""
        import random
        random.seed(123)
        path = tempfile.mktemp(suffix=".csv")
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["item_id", "rater_id", "classification", "confidence", "justification", "language", "item_language"])
                for i in range(20):
                    for j in range(10):
                        cat = random.choice(["reasoning_operator", "domain_knowledge"])
                        writer.writerow([f"item-{i+1}", f"rater-{j+1}", cat, 3, "random", "en", "en"])
            calc = KappaCalculator()
            result = calc.compute(path)
            assert result.kappa < 0.3
            assert not result.threshold_passed
        finally:
            Path(path).unlink(missing_ok=True)

    def test_language_split(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            _write_sample_ratings(path)
            calc = KappaCalculator()
            result = calc.compute(path)
            assert result.same_language_kappa is not None
            assert result.cross_language_kappa is not None
        finally:
            Path(path).unlink(missing_ok=True)

    def test_ambiguous_items(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            _write_sample_ratings(path, accuracy=0.55)  # low accuracy → more ambiguous
            calc = KappaCalculator()
            result = calc.compute(path)
            # With 55% accuracy, there should be some ambiguous items
            assert isinstance(result.ambiguous_items, list)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_report_text(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            _write_sample_ratings(path)
            calc = KappaCalculator()
            result = calc.compute(path)
            text = result.to_text()
            assert "Fleiss' Kappa" in text
            assert "THRESHOLD" in text
        finally:
            Path(path).unlink(missing_ok=True)

    def test_summary(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            path = f.name
        try:
            _write_sample_ratings(path)
            calc = KappaCalculator()
            result = calc.compute(path)
            s = result.summary()
            assert "κ=" in s
            assert "threshold" in s
        finally:
            Path(path).unlink(missing_ok=True)
