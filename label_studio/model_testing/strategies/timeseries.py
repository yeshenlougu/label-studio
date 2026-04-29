from datetime import datetime
from typing import Dict, List, Tuple

from .base import BaseSplitStrategy


class TimeSeriesSplitStrategy(BaseSplitStrategy):
    """时间序列切割策略 - 按时间顺序切割"""

    @classmethod
    def get_strategy_type(cls) -> str:
        return 'timeseries'

    @classmethod
    def get_name(cls) -> str:
        return '时间序列切割'

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
                    'name': 'time_field',
                    'type': 'string',
                    'label': '时间字段',
                    'default': 'created_at',
                    'description': '用于排序的时间字段',
                },
                {
                    'name': 'order',
                    'type': 'select',
                    'label': '排序方式',
                    'default': 'asc',
                    'options': [
                        {'value': 'asc', 'label': '升序 (旧->新)'},
                        {'value': 'desc', 'label': '降序 (新->旧)'},
                    ],
                },
            ]
        }

    def split(
        self, task_ids: List[int], config: Dict, time_map: Dict[int, datetime] = None
    ) -> Tuple[List[int], List[int]]:
        """
        执行时间序列切割

        Args:
            task_ids: 任务ID列表
            config: 切割配置参数
            time_map: 任务ID到时间的映射 {task_id: datetime}

        Returns:
            (train_task_ids, test_task_ids)
        """
        test_ratio = config.get('test_ratio', 0.2)
        order = config.get('order', 'asc')

        if not time_map:
            task_ids = list(task_ids)
        else:
            task_ids = sorted(
                task_ids,
                key=lambda x: time_map.get(x, datetime.min),
                reverse=(order == 'desc'),
            )

        split_idx = int(len(task_ids) * test_ratio)

        if order == 'asc':
            test_ids = task_ids[:split_idx]
            train_ids = task_ids[split_idx:]
        else:
            test_ids = task_ids[:split_idx]
            train_ids = task_ids[split_idx:]

        return train_ids, test_ids

    def validate_config(self, config: Dict) -> bool:
        test_ratio = config.get('test_ratio', 0.2)
        if not 0 < test_ratio < 1:
            return False
        return True
