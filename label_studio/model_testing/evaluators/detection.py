from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .base import BaseEvaluator


def calculate_iou(box1: Dict, box2: Dict) -> float:
    """计算两个边界框的 IoU"""
    x1_1, y1_1 = box1.get('x', 0), box1.get('y', 0)
    x2_1 = x1_1 + box1.get('width', 0)
    y2_1 = y1_1 + box1.get('height', 0)

    x1_2, y1_2 = box2.get('x', 0), box2.get('y', 0)
    x2_2 = x1_2 + box2.get('width', 0)
    y2_2 = y1_2 + box2.get('height', 0)

    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


class DetectionEvaluator(BaseEvaluator):
    """目标检测评估器"""

    @classmethod
    def get_evaluator_type(cls) -> str:
        return 'detection'

    @classmethod
    def get_name(cls) -> str:
        return '目标检测评估'

    @classmethod
    def get_supported_task_types(cls) -> List[str]:
        return ['rectanglelabels', 'polygonlabels', 'keypointlabels', 'brushlabels', 'hypertextlabels']

    @classmethod
    def get_config_schema(cls) -> Dict:
        return {
            'fields': [
                {
                    'name': 'iou_threshold',
                    'type': 'number',
                    'label': 'IoU 阈值',
                    'default': 0.5,
                    'min': 0.1,
                    'max': 0.95,
                    'step': 0.05,
                },
                {
                    'name': 'score_threshold',
                    'type': 'number',
                    'label': '置信度阈值',
                    'default': 0.5,
                    'min': 0.0,
                    'max': 1.0,
                    'step': 0.1,
                },
            ]
        }

    def extract_boxes_from_result(self, result: List[Dict]) -> Dict[str, List[Dict]]:
        """从标注结果中提取边界框，按标签分组"""
        boxes_by_label = defaultdict(list)

        for item in result or []:
            if item.get('type') == 'rectanglelabels':
                value = item.get('value', {})
                labels = value.get('rectanglelabels', [])
                box = {
                    'x': value.get('x', 0),
                    'y': value.get('y', 0),
                    'width': value.get('width', 0),
                    'height': value.get('height', 0),
                }
                for label in labels:
                    boxes_by_label[label].append(box)

        return boxes_by_label

    def match_predictions_to_ground_truth(
        self,
        gt_boxes: List[Dict],
        pred_boxes: List[Dict],
        iou_threshold: float,
    ) -> Tuple[int, int, int]:
        """
        匹配预测框到真实框

        Returns:
            (true_positives, false_positives, false_negatives)
        """
        if not gt_boxes and not pred_boxes:
            return 0, 0, 0
        if not gt_boxes:
            return 0, len(pred_boxes), 0
        if not pred_boxes:
            return 0, 0, len(gt_boxes)

        matched_gt = set()
        matched_pred = set()

        for pred_idx, pred_box in enumerate(pred_boxes):
            best_iou = 0
            best_gt_idx = -1

            for gt_idx, gt_box in enumerate(gt_boxes):
                if gt_idx in matched_gt:
                    continue
                iou = calculate_iou(pred_box, gt_box)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx

            if best_iou >= iou_threshold:
                matched_gt.add(best_gt_idx)
                matched_pred.add(pred_idx)

        tp = len(matched_pred)
        fp = len(pred_boxes) - len(matched_pred)
        fn = len(gt_boxes) - len(matched_gt)

        return tp, fp, fn

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
        执行目标检测评估

        Args:
            ground_truths: 人工标注结果列表，每个元素是 task 的标注结果
            predictions: 模型预测结果列表，每个元素是 task 的预测结果
            task_ids: 任务ID列表
            **kwargs: iou_threshold, score_threshold

        Returns:
            评估结果字典
        """
        iou_threshold = kwargs.get('iou_threshold', 0.5)
        score_threshold = kwargs.get('score_threshold', 0.5)

        all_labels = set()
        per_label_stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
        error_samples = []

        for idx, (gt, pred) in enumerate(zip(ground_truths, predictions)):
            gt_boxes_by_label = self.extract_boxes_from_result(gt)
            pred_boxes_by_label = self.extract_boxes_from_result(pred)

            all_labels.update(gt_boxes_by_label.keys())
            all_labels.update(pred_boxes_by_label.keys())

            task_has_error = False
            for label in all_labels:
                gt_boxes = gt_boxes_by_label.get(label, [])
                pred_boxes = pred_boxes_by_label.get(label, [])

                tp, fp, fn = self.match_predictions_to_ground_truth(
                    gt_boxes, pred_boxes, iou_threshold
                )
                per_label_stats[label]['tp'] += tp
                per_label_stats[label]['fp'] += fp
                per_label_stats[label]['fn'] += fn

                if fp > 0 or fn > 0:
                    task_has_error = True

            if task_has_error and task_ids and idx < len(task_ids):
                error_samples.append(task_ids[idx])

        per_class_metrics = {}
        total_tp, total_fp, total_fn = 0, 0, 0

        for label in all_labels:
            stats = per_label_stats[label]
            metrics = self.calculate_metrics(stats['tp'], stats['fp'], stats['fn'])
            per_class_metrics[label] = metrics
            total_tp += stats['tp']
            total_fp += stats['fp']
            total_fn += stats['fn']

        overall_metrics = self.calculate_metrics(total_tp, total_fp, total_fn)

        labels_list = sorted(all_labels)
        confusion_matrix = []
        if len(labels_list) > 0:
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
                'iou_threshold': iou_threshold,
                'score_threshold': score_threshold,
            },
        }
