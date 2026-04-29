from collections import defaultdict
from typing import Dict, List

from .base import BaseEvaluator


class ClassificationEvaluator(BaseEvaluator):
    """分类评估器"""

    @classmethod
    def get_evaluator_type(cls) -> str:
        return 'classification'

    @classmethod
    def get_name(cls) -> str:
        return '分类评估'

    @classmethod
    def get_supported_task_types(cls) -> List[str]:
        return ['choices', 'rating', 'taxonomy']

    @classmethod
    def get_config_schema(cls) -> Dict:
        return {
            'fields': [
                {
                    'name': 'average',
                    'type': 'select',
                    'label': '平均方式',
                    'default': 'macro',
                    'options': [
                        {'value': 'macro', 'label': '宏平均'},
                        {'value': 'micro', 'label': '微平均'},
                        {'value': 'weighted', 'label': '加权平均'},
                    ],
                },
            ]
        }

    def extract_labels_from_result(self, result: List[Dict]) -> List[str]:
        """从标注结果中提取标签"""
        labels = []
        for item in result or []:
            item_type = item.get('type')
            value = item.get('value', {})

            if item_type == 'choices':
                labels.extend(value.get('choices', []))
            elif item_type == 'taxonomy':
                labels.extend(value.get('taxonomy', []))
            elif item_type == 'rating':
                labels.append(str(value.get('rating', '')))

        return labels

    def calculate_metrics(self, tp: int, fp: int, fn: int) -> Dict:
        """计算精确率、召回率、F1"""
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
        }

    def evaluate(
        self,
        ground_truths: List[Dict],
        predictions: List[Dict],
        task_ids: List[int] = None,
        **kwargs,
    ) -> Dict:
        """
        执行分类评估
        """
        average = kwargs.get('average', 'macro')

        all_labels = set()
        per_label_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
        error_samples = []

        correct_count = 0
        total_count = 0

        for idx, (gt, pred) in enumerate(zip(ground_truths, predictions)):
            gt_labels = set(self.extract_labels_from_result(gt))
            pred_labels = set(self.extract_labels_from_result(pred))

            all_labels.update(gt_labels)
            all_labels.update(pred_labels)

            if gt_labels == pred_labels:
                correct_count += 1
            else:
                if task_ids and idx < len(task_ids):
                    error_samples.append(task_ids[idx])

            total_count += 1

            for label in all_labels:
                in_gt = label in gt_labels
                in_pred = label in pred_labels

                if in_gt and in_pred:
                    per_label_stats[label]['tp'] += 1
                elif in_pred and not in_gt:
                    per_label_stats[label]['fp'] += 1
                elif in_gt and not in_pred:
                    per_label_stats[label]['fn'] += 1

        per_class_metrics = {}
        total_tp, total_fp, total_fn = 0, 0, 0

        for label in all_labels:
            stats = per_label_stats[label]
            metrics = self.calculate_metrics(stats['tp'], stats['fp'], stats['fn'])
            per_class_metrics[label] = metrics
            total_tp += stats['tp']
            total_fp += stats['fp']
            total_fn += stats['fn']

        accuracy = correct_count / total_count if total_count > 0 else 0.0

        if average == 'micro':
            overall_metrics = self.calculate_metrics(total_tp, total_fp, total_fn)
            overall_metrics['accuracy'] = accuracy
        else:
            precisions = [m['precision'] for m in per_class_metrics.values()]
            recalls = [m['recall'] for m in per_class_metrics.values()]
            f1s = [m['f1'] for m in per_class_metrics.values()]

            n = len(per_class_metrics)
            if average == 'macro':
                overall_metrics = {
                    'precision': sum(precisions) / n if n > 0 else 0.0,
                    'recall': sum(recalls) / n if n > 0 else 0.0,
                    'f1': sum(f1s) / n if n > 0 else 0.0,
                    'accuracy': accuracy,
                }
            else:
                total_samples = sum(
                    per_label_stats[l]['tp'] + per_label_stats[l]['fn'] for l in all_labels
                )
                weights = {
                    l: (per_label_stats[l]['tp'] + per_label_stats[l]['fn']) / total_samples
                    if total_samples > 0
                    else 0
                    for l in all_labels
                }

                overall_metrics = {
                    'precision': sum(
                        per_class_metrics[l]['precision'] * weights[l] for l in all_labels
                    ),
                    'recall': sum(recalls[i] * weights[list(all_labels)[i]] for i in range(n)),
                    'f1': sum(f1s[i] * weights[list(all_labels)[i]] for i in range(n)),
                    'accuracy': accuracy,
                }

        labels_list = sorted(all_labels)
        confusion_matrix = {
            'labels': labels_list,
            'matrix': [[0] * len(labels_list) for _ in range(len(labels_list))],
        }

        return {
            'metrics': overall_metrics,
            'per_class_metrics': per_class_metrics,
            'confusion_matrix': confusion_matrix,
            'error_samples': error_samples,
            'config': {
                'average': average,
            },
        }
