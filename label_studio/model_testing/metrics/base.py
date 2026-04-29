from typing import Dict, List


class BaseMetric:
    """指标基类"""

    @staticmethod
    def calculate_precision(tp: int, fp: int) -> float:
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0

    @staticmethod
    def calculate_recall(tp: int, fn: int) -> float:
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0

    @staticmethod
    def calculate_f1(precision: float, recall: float) -> float:
        return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    @staticmethod
    def calculate_accuracy(correct: int, total: int) -> float:
        return correct / total if total > 0 else 0.0
