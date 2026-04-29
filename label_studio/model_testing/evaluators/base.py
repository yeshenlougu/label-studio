from abc import ABC, abstractmethod
from typing import Dict, List


class BaseEvaluator(ABC):
    """评估器基类"""

    _registry = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        evaluator_type = cls.get_evaluator_type()
        if evaluator_type:
            cls._registry[evaluator_type] = cls

    @classmethod
    def get_registry(cls):
        return cls._registry

    @classmethod
    def get_evaluator(cls, evaluator_type: str):
        return cls._registry.get(evaluator_type)

    @classmethod
    @abstractmethod
    def get_evaluator_type(cls) -> str:
        """评估器类型标识"""
        pass

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """评估器显示名称"""
        pass

    @classmethod
    @abstractmethod
    def get_supported_task_types(cls) -> List[str]:
        """支持的任务类型"""
        pass

    @abstractmethod
    def evaluate(
        self,
        ground_truths: List[Dict],
        predictions: List[Dict],
        task_ids: List[int] = None,
        **kwargs,
    ) -> Dict:
        """
        执行评估

        Args:
            ground_truths: 人工标注结果列表
            predictions: 模型预测结果列表
            task_ids: 任务ID列表
            **kwargs: 额外参数

        Returns:
            {
                'metrics': {...},
                'per_class_metrics': {...},
                'confusion_matrix': [...],
                'error_samples': [...]
            }
        """
        pass

    @classmethod
    def get_config_schema(cls) -> Dict:
        """返回配置表单的 JSON Schema"""
        return {'fields': []}
