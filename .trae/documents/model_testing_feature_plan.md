# 模型测试功能实施计划

## 概述

在 Label Studio 现有的自动标注功能基础上，添加模型测试功能，包括：
1. **数据集切割**：将数据集划分为训练集和测试集，支持多种切割策略
2. **模型准确率评估**：在测试集上自动标注，与人工标注对比，计算准确率指标

## 当前状态分析

### 现有相关功能

| 模块 | 功能 | 文件位置 |
|------|------|----------|
| 自动标注 | ML后端预测、预测转标注 | `label_studio/ml/`, `label_studio/data_manager/actions/predictions_to_annotations.py` |
| 数据管理 | 任务过滤、视图、Actions | `label_studio/data_manager/` |
| 数据导出 | 多格式导出 | `label_studio/data_export/` |
| 权限系统 | 角色权限控制 | `label_studio/core/permissions.py` |

### 现有数据模型

- `Task`: 任务数据，包含 `data`, `meta`, `project` 等字段
- `Annotation`: 标注结果，包含 `result`, `ground_truth`, `completed_by` 等字段
- `Prediction`: 预测结果，包含 `result`, `model_version`, `score` 等字段
- `View`: 视图/标签页配置

### Actions 注册机制

系统通过 `register_action()` 函数注册操作，支持：
- 权限控制
- 对话框表单
- 异步执行

## 提议变更

### 1. 新建 Django App: `model_testing`

创建独立的 Django 应用模块，包含所有模型测试相关功能。

**目录结构：**
```
label_studio/model_testing/
├── __init__.py
├── apps.py
├── models.py           # 数据模型
├── serializers.py      # API 序列化器
├── api.py              # API 端点
├── urls.py             # URL 路由
├── strategies/         # 切割策略
│   ├── __init__.py
│   ├── base.py         # 基类
│   ├── random.py       # 随机切割
│   ├── stratified.py   # 分层切割
│   └── timeseries.py   # 时间序列切割
├── evaluators/         # 评估器
│   ├── __init__.py
│   ├── base.py         # 基类
│   ├── classification.py  # 分类评估
│   ├── detection.py    # 目标检测评估
│   └── ner.py          # NER评估（预留）
├── metrics/            # 评估指标
│   ├── __init__.py
│   ├── base.py
│   └── classification.py
├── utils.py            # 工具函数
└── tests/              # 测试
```

### 2. 数据模型设计

#### 2.1 DatasetSplit（数据集切割配置）

```python
class DatasetSplit(models.Model):
    """数据集切割配置"""
    class SplitType(models.TextChoices):
        RANDOM = 'random', '随机切割'
        STRATIFIED = 'stratified', '分层切割'
        TIMESERIES = 'timeseries', '时间序列切割'
        MANUAL = 'manual', '手动指定'
    
    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='dataset_splits')
    name = models.CharField(max_length=255)  # 切割名称
    split_type = models.CharField(max_length=32, choices=SplitType.choices)
    config = models.JSONField(default=dict)  # 切割配置参数
    status = models.CharField(max_length=32, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 统计信息
    total_tasks = models.IntegerField(default=0)
    train_tasks = models.IntegerField(default=0)
    test_tasks = models.IntegerField(default=0)
```

#### 2.2 DatasetSplitItem（切割项）

```python
class DatasetSplitItem(models.Model):
    """切割项 - 每个任务的分组信息"""
    class Group(models.TextChoices):
        TRAIN = 'train', '训练集'
        TEST = 'test', '测试集'
    
    split = models.ForeignKey(DatasetSplit, on_delete=models.CASCADE, related_name='items')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='split_items')
    group = models.CharField(max_length=16, choices=Group.choices)
    
    class Meta:
        unique_together = ['split', 'task']
```

#### 2.3 ModelEvaluation（模型评估）

```python
class ModelEvaluation(models.Model):
    """模型评估记录"""
    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        IN_PROGRESS = 'in_progress', '进行中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='evaluations')
    split = models.ForeignKey(DatasetSplit, on_delete=models.CASCADE, related_name='evaluations')
    name = models.CharField(max_length=255)
    model_versions = models.JSONField(default=list)  # 评估的模型版本列表
    
    status = models.CharField(max_length=32, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    
    # 汇总指标
    summary_metrics = models.JSONField(default=dict)
```

#### 2.4 EvaluationResult（评估结果详情）

```python
class EvaluationResult(models.Model):
    """评估结果详情"""
    evaluation = models.ForeignKey(ModelEvaluation, on_delete=models.CASCADE, related_name='results')
    model_version = models.CharField(max_length=255)
    
    # 整体指标
    metrics = models.JSONField(default=dict)  # {accuracy, precision, recall, f1, ...}
    
    # 分类别指标
    per_class_metrics = models.JSONField(default=dict)
    
    # 混淆矩阵
    confusion_matrix = models.JSONField(default=list)
    
    # 错误样本
    error_samples = models.JSONField(default=list)  # 错误预测的任务ID列表
```

#### 2.5 EvaluationReport（评估报告）

```python
class EvaluationReport(models.Model):
    """评估报告"""
    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        HTML = 'html', 'HTML'
        JSON = 'json', 'JSON'
        CSV = 'csv', 'CSV'
    
    evaluation = models.ForeignKey(ModelEvaluation, on_delete=models.CASCADE, related_name='reports')
    format = models.CharField(max_length=16, choices=Format.choices)
    file = models.FileField(upload_to='evaluation_reports/')
    created_at = models.DateTimeField(auto_now_add=True)
```

### 3. 切割策略设计（策略模式）

#### 3.1 基类定义

```python
# label_studio/model_testing/strategies/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from tasks.models import Task

class BaseSplitStrategy(ABC):
    """切割策略基类"""
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """策略名称"""
        pass
    
    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict:
        """返回配置表单的 JSON Schema"""
        pass
    
    @abstractmethod
    def split(self, tasks: List[Task], config: Dict) -> Tuple[List[int], List[int]]:
        """
        执行切割
        Returns: (train_task_ids, test_task_ids)
        """
        pass
```

#### 3.2 随机切割策略

```python
# label_studio/model_testing/strategies/random.py
import random
from .base import BaseSplitStrategy

class RandomSplitStrategy(BaseSplitStrategy):
    
    @classmethod
    def get_name(cls) -> str:
        return '随机切割'
    
    @classmethod
    def get_config_schema(cls) -> Dict:
        return {
            'fields': [
                {'name': 'test_ratio', 'type': 'number', 'label': '测试集比例', 'default': 0.2, 'min': 0.1, 'max': 0.5},
                {'name': 'random_seed', 'type': 'number', 'label': '随机种子', 'default': 42},
                {'name': 'shuffle', 'type': 'boolean', 'label': '随机打乱', 'default': True},
            ]
        }
    
    def split(self, tasks, config):
        test_ratio = config.get('test_ratio', 0.2)
        seed = config.get('random_seed', 42)
        shuffle = config.get('shuffle', True)
        
        task_ids = [t.id for t in tasks]
        if shuffle:
            random.seed(seed)
            random.shuffle(task_ids)
        
        split_idx = int(len(task_ids) * test_ratio)
        test_ids = task_ids[:split_idx]
        train_ids = task_ids[split_idx:]
        
        return train_ids, test_ids
```

### 4. 评估器设计（策略模式）

#### 4.1 基类定义

```python
# label_studio/model_testing/evaluators/base.py
from abc import ABC, abstractmethod
from typing import Dict, List
from tasks.models import Task, Annotation, Prediction

class BaseEvaluator(ABC):
    """评估器基类"""
    
    @classmethod
    @abstractmethod
    def get_supported_task_types(cls) -> List[str]:
        """支持的任务类型"""
        pass
    
    @abstractmethod
    def evaluate(self, ground_truths: List[Dict], predictions: List[Dict]) -> Dict:
        """
        执行评估
        Returns: {
            'metrics': {...},
            'per_class_metrics': {...},
            'confusion_matrix': [...],
            'error_samples': [...]
        }
        """
        pass
```

#### 4.2 目标检测评估器

```python
# label_studio/model_testing/evaluators/detection.py
from .base import BaseEvaluator

class DetectionEvaluator(BaseEvaluator):
    """目标检测评估器"""
    
    @classmethod
    def get_supported_task_types(cls):
        return ['rectanglelabels', 'polygonlabels', 'keypointlabels', 'brushlabels']
    
    def evaluate(self, ground_truths, predictions, iou_threshold=0.5):
        results = {
            'metrics': {},
            'per_class_metrics': {},
            'confusion_matrix': [],
            'error_samples': []
        }
        
        # 计算 mAP, precision, recall, F1
        # ...
        
        return results
```

### 5. API 端点设计

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/projects/{id}/splits/` | GET, POST | 获取/创建切割配置 |
| `/api/projects/{id}/splits/{split_id}/` | GET, DELETE | 获取/删除切割详情 |
| `/api/projects/{id}/splits/{split_id}/tasks/` | GET | 获取切割后的任务列表 |
| `/api/projects/{id}/evaluations/` | GET, POST | 获取/创建评估 |
| `/api/projects/{id}/evaluations/{eval_id}/` | GET | 获取评估详情 |
| `/api/projects/{id}/evaluations/{eval_id}/run/` | POST | 执行评估 |
| `/api/projects/{id}/evaluations/{eval_id}/reports/` | GET, POST | 获取/生成报告 |
| `/api/strategies/` | GET | 获取可用切割策略 |
| `/api/evaluators/` | GET | 获取可用评估器 |

### 6. 前端设计

#### 6.1 新增页面/组件

```
web/libs/labelstudio/feature/
└── model-testing/
    ├── components/
    │   ├── SplitList/
    │   │   ├── SplitList.tsx        # 切割列表
    │   │   ├── SplitCard.tsx        # 切割卡片
    │   │   └── SplitForm.tsx        # 切割配置表单
    │   ├── SplitDetail/
    │   │   └── SplitDetail.tsx      # 切割详情（训练/测试集预览）
    │   ├── EvaluationList/
    │   │   ├── EvaluationList.tsx   # 评估列表
    │   │   └── EvaluationCard.tsx   # 评估卡片
    │   ├── EvaluationDetail/
    │   │   ├── EvaluationDetail.tsx # 评估详情
    │   │   ├── MetricsChart.tsx     # 指标图表
    │   │   ├── ConfusionMatrix.tsx  # 混淆矩阵
    │   │   └── ErrorSamples.tsx     # 错误样本
    │   └── ReportExport/
    │       └── ReportExport.tsx     # 报告导出
    ├── pages/
    │   ├── SplitPage.tsx            # 数据集切割页面
    │   └── EvaluationPage.tsx       # 模型测试页面
    └── store/
        └── modelTestingStore.ts     # 状态管理
```

#### 6.2 集成到数据管理器

在数据管理器工具栏添加 "数据集划分" 按钮，点击后进入切割界面。

### 7. 权限配置

在 `core/permissions.py` 中添加新权限：

```python
# 新增权限
MODEL_TESTING_VIEW = 'model_testing.view'
MODEL_TESTING_CREATE = 'model_testing.create'
MODEL_TESTING_DELETE = 'model_testing.delete'
MODEL_TESTING_RUN = 'model_testing.run'
```

支持通过组织/项目配置控制权限。

### 8. 数据库迁移

需要创建以下迁移文件：
1. 创建 `model_testing` app 的初始迁移
2. 创建 `DatasetSplit`, `DatasetSplitItem`, `ModelEvaluation`, `EvaluationResult`, `EvaluationReport` 表

## 实施步骤

### 阶段一：后端基础架构（预计工作量：中）

1. 创建 `model_testing` Django app
2. 实现数据模型和迁移
3. 实现切割策略基类和随机切割策略
4. 实现评估器基类和目标检测评估器
5. 实现 API 端点
6. 添加权限控制

### 阶段二：前端界面（预计工作量：中）

1. 创建前端组件结构
2. 实现切割列表和配置表单
3. 实现切割详情页面
4. 实现评估列表和详情页面
5. 实现指标图表和混淆矩阵展示
6. 集成到数据管理器

### 阶段三：评估报告和扩展（预计工作量：小）

1. 实现报告生成（PDF/HTML/JSON/CSV）
2. 实现历史记录查询
3. 添加分层切割策略
4. 添加时间序列切割策略

### 阶段四：测试和文档（预计工作量：小）

1. 编写单元测试
2. 编写集成测试
3. 编写 API 文档

## 假设与决策

### 假设
1. 用户已有标注好的数据集（包含 ground_truth 标注）
2. 用户已配置 ML 后端或模型提供商
3. 项目配置了正确的标注类型

### 决策
1. **独立模块**：创建独立的 `model_testing` app，便于维护和扩展
2. **策略模式**：切割策略和评估器都使用策略模式，支持灵活扩展
3. **数据库存储**：所有切割配置和评估结果存储在数据库，支持历史查询
4. **异步执行**：大规模评估使用异步任务队列（RQ）
5. **第一版范围**：优先支持图像标注（目标检测）评估

## 验证步骤

1. **功能测试**
   - 创建切割配置，验证任务正确分组
   - 执行评估，验证指标计算正确
   - 导出报告，验证格式正确

2. **性能测试**
   - 大规模数据集（10000+ 任务）切割性能
   - 大规模评估执行时间

3. **权限测试**
   - 验证不同角色用户的访问权限

## 文件变更清单

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| `label_studio/model_testing/__init__.py` | App 初始化 |
| `label_studio/model_testing/apps.py` | App 配置 |
| `label_studio/model_testing/models.py` | 数据模型 |
| `label_studio/model_testing/serializers.py` | 序列化器 |
| `label_studio/model_testing/api.py` | API 视图 |
| `label_studio/model_testing/urls.py` | URL 路由 |
| `label_studio/model_testing/strategies/base.py` | 切割策略基类 |
| `label_studio/model_testing/strategies/random.py` | 随机切割策略 |
| `label_studio/model_testing/strategies/stratified.py` | 分层切割策略 |
| `label_studio/model_testing/evaluators/base.py` | 评估器基类 |
| `label_studio/model_testing/evaluators/detection.py` | 目标检测评估器 |
| `label_studio/model_testing/metrics/base.py` | 指标基类 |
| `label_studio/model_testing/metrics/classification.py` | 分类指标 |
| `web/libs/labelstudio/feature/model-testing/` | 前端组件目录 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `label_studio/core/permissions.py` | 添加模型测试权限 |
| `label_studio/core/settings/base.py` | 注册 model_testing app |
| `label_studio/core/urls.py` | 添加 model_testing URL |
| `web/libs/datamanager/src/components/MainView/` | 添加入口按钮 |
