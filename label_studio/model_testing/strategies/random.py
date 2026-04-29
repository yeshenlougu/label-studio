import random
from typing import Dict, List, Tuple

from .base import BaseSplitStrategy


class RandomSplitStrategy(BaseSplitStrategy):
    """随机切割策略"""

    @classmethod
    def get_strategy_type(cls) -> str:
        return 'random'

    @classmethod
    def get_name(cls) -> str:
        return '随机切割'

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
                    'name': 'shuffle',
                    'type': 'boolean',
                    'label': '随机打乱',
                    'default': True,
                },
            ]
        }

    def split(self, task_ids: List[int], config: Dict) -> Tuple[List[int], List[int]]:
        test_ratio = config.get('test_ratio', 0.2)
        seed = config.get('random_seed', 42)
        shuffle = config.get('shuffle', True)

        task_ids = list(task_ids)
        if shuffle:
            random.seed(seed)
            random.shuffle(task_ids)

        split_idx = int(len(task_ids) * test_ratio)
        test_ids = task_ids[:split_idx]
        train_ids = task_ids[split_idx:]

        return train_ids, test_ids

    def validate_config(self, config: Dict) -> bool:
        test_ratio = config.get('test_ratio', 0.2)
        if not 0 < test_ratio < 1:
            return False
        return True
