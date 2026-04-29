from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class BaseSplitStrategy(ABC):
    """切割策略基类"""

    _registry = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        strategy_type = cls.get_strategy_type()
        if strategy_type:
            cls._registry[strategy_type] = cls

    @classmethod
    def get_registry(cls):
        return cls._registry

    @classmethod
    def get_strategy(cls, strategy_type: str):
        return cls._registry.get(strategy_type)

    @classmethod
    @abstractmethod
    def get_strategy_type(cls) -> str:
        """策略类型标识"""
        pass

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """策略显示名称"""
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict:
        """返回配置表单的 JSON Schema"""
        pass

    @abstractmethod
    def split(self, task_ids: List[int], config: Dict) -> Tuple[List[int], List[int]]:
        """
        执行切割

        Args:
            task_ids: 任务ID列表
            config: 切割配置参数

        Returns:
            (train_task_ids, test_task_ids)
        """
        pass

    def validate_config(self, config: Dict) -> bool:
        """验证配置参数"""
        return True
