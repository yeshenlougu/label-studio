from collections import Counter
from typing import Dict, List, Tuple

from .base import BaseSplitStrategy


class StratifiedSplitStrategy(BaseSplitStrategy):
    """分层切割策略 - 按标签比例分层切割"""

    @classmethod
    def get_strategy_type(cls) -> str:
        return 'stratified'

    @classmethod
    def get_name(cls) -> str:
        return '分层切割'

    @classmethod
    def get_config_schema(cls) -> Dict:
        return {
            'fields': [
                {
                    'name': 'test_ratio',
                    'type': 'number',
                    'label': '测试集比例',
                    'default': 0.2,
                    'min': 0.1,
                    'max': 0.5,
                    'step': 0.05,
                },
                {
                    'name': 'random_seed',
                    'type': 'number',
                    'label': '随机种子',
                    'default': 42,
                },
                {
                    'name': 'label_field',
                    'type': 'string',
                    'label': '标签字段',
                    'default': 'label',
                    'description': '用于分层的标签字段名称',
                },
            ]
        }

    def split(
        self, task_ids: List[int], config: Dict, label_map: Dict[int, str] = None
    ) -> Tuple[List[int], List[int]]:
        """
        执行分层切割

        Args:
            task_ids: 任务ID列表
            config: 切割配置参数
            label_map: 任务ID到标签的映射 {task_id: label}

        Returns:
            (train_task_ids, test_task_ids)
        """
        import random

        test_ratio = config.get('test_ratio', 0.2)
        seed = config.get('random_seed', 42)

        random.seed(seed)

        if not label_map:
            return RandomSplitStrategy().split(task_ids, config)

        label_groups = {}
        for task_id in task_ids:
            label = label_map.get(task_id, 'unknown')
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(task_id)

        train_ids = []
        test_ids = []

        for label, ids in label_groups.items():
            random.shuffle(ids)
            split_idx = int(len(ids) * test_ratio)
            test_ids.extend(ids[:split_idx])
            train_ids.extend(ids[split_idx:])

        random.shuffle(train_ids)
        random.shuffle(test_ids)

        return train_ids, test_ids

    def validate_config(self, config: Dict) -> bool:
        test_ratio = config.get('test_ratio', 0.2)
        if not 0 < test_ratio < 1:
            return False
        return True
