import logging
from datetime import datetime

from core.permissions import ViewClassPermission, all_permissions
from core.redis import start_job_async_or_sync
from core.utils.common import load_func
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from projects.models import Project
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from tasks.models import Annotation, Prediction, Task

from .evaluators import ClassificationEvaluator, DetectionEvaluator
from .models import DatasetSplit, DatasetSplitItem, EvaluationReport, ModelEvaluation
from .serializers import (
    DatasetSplitCreateSerializer,
    DatasetSplitDetailSerializer,
    DatasetSplitSerializer,
    EvaluatorSerializer,
    EvaluationReportSerializer,
    ModelEvaluationCreateSerializer,
    ModelEvaluationSerializer,
    StrategySerializer,
)
from .strategies import BaseSplitStrategy, RandomSplitStrategy, StratifiedSplitStrategy, TimeSeriesSplitStrategy

logger = logging.getLogger(__name__)


class DatasetSplitViewSet(viewsets.ModelViewSet):
    """数据集切割视图集"""

    queryset = DatasetSplit.objects.all()
    serializer_class = DatasetSplitSerializer
    permission_required = ViewClassPermission(
        GET=all_permissions.model_testing_view,
        POST=all_permissions.model_testing_create,
        PATCH=all_permissions.model_testing_change,
        DELETE=all_permissions.model_testing_delete,
    )

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return DatasetSplit.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return DatasetSplitCreateSerializer
        if self.action == 'retrieve':
            return DatasetSplitDetailSerializer
        return DatasetSplitSerializer

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        split = serializer.save(project=project, created_by=self.request.user)
        self._execute_split(split, project)

    def _execute_split(self, split: DatasetSplit, project: Project):
        """执行切割"""
        try:
            tasks = project.tasks.all()
            task_ids = list(tasks.values_list('id', flat=True))

            strategy_cls = BaseSplitStrategy.get_strategy(split.split_type)
            if not strategy_cls:
                strategy_cls = RandomSplitStrategy

            strategy = strategy_cls()
            train_ids, test_ids = strategy.split(task_ids, split.config)

            items = []
            for task_id in train_ids:
                items.append(
                    DatasetSplitItem(
                        split=split,
                        task_id=task_id,
                        group=DatasetSplitItem.Group.TRAIN,
                    )
                )
            for task_id in test_ids:
                items.append(
                    DatasetSplitItem(
                        split=split,
                        task_id=task_id,
                        group=DatasetSplitItem.Group.TEST,
                    )
                )

            DatasetSplitItem.objects.bulk_create(items)

            split.total_tasks = len(task_ids)
            split.train_tasks = len(train_ids)
            split.test_tasks = len(test_ids)
            split.status = DatasetSplit.Status.COMPLETED
            split.save()

        except Exception as e:
            logger.exception(f'Error executing split: {e}')
            split.status = DatasetSplit.Status.FAILED
            split.save()

    @action(detail=True, methods=['get'])
    def tasks(self, request, project_id=None, pk=None):
        """获取切割后的任务列表"""
        split = self.get_object()
        group = request.query_params.get('group')

        items = split.items.all()
        if group:
            items = items.filter(group=group)

        task_ids = list(items.values_list('task_id', flat=True))
        tasks = Task.objects.filter(id__in=task_ids)

        return Response(
            {
                'split_id': split.id,
                'group': group,
                'tasks': [{'id': t.id, 'data': t.data} for t in tasks],
            }
        )


class ModelEvaluationViewSet(viewsets.ModelViewSet):
    """模型评估视图集"""

    queryset = ModelEvaluation.objects.all()
    serializer_class = ModelEvaluationSerializer
    permission_required = ViewClassPermission(
        GET=all_permissions.model_testing_view,
        POST=all_permissions.model_testing_create,
        PATCH=all_permissions.model_testing_change,
        DELETE=all_permissions.model_testing_delete,
    )

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return ModelEvaluation.objects.filter(project_id=project_id)

    def get_serializer_class(self):
        if self.action == 'create':
            return ModelEvaluationCreateSerializer
        return ModelEvaluationSerializer

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        evaluation = serializer.save(project=project, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def run(self, request, project_id=None, pk=None):
        """执行评估"""
        evaluation = self.get_object()

        if evaluation.status == ModelEvaluation.Status.IN_PROGRESS:
            return Response({'detail': '评估正在进行中'}, status=status.HTTP_400_BAD_REQUEST)

        evaluation.status = ModelEvaluation.Status.IN_PROGRESS
        evaluation.save()

        start_job_async_or_sync(
            run_evaluation_task,
            evaluation.id,
            queue_name='default',
        )

        return Response({'detail': '评估已开始', 'evaluation_id': evaluation.id})

    @action(detail=True, methods=['get', 'post'])
    def reports(self, request, project_id=None, pk=None):
        """获取或生成评估报告"""
        evaluation = self.get_object()

        if request.method == 'GET':
            reports = evaluation.reports.all()
            serializer = EvaluationReportSerializer(reports, many=True)
            return Response(serializer.data)

        format_type = request.data.get('format', 'json')
        report = EvaluationReport.objects.create(
            evaluation=evaluation,
            format=format_type,
        )

        return Response(
            {
                'id': report.id,
                'format': report.format,
                'status': 'created',
            },
            status=status.HTTP_201_CREATED,
        )


def run_evaluation_task(evaluation_id: int):
    """执行评估任务"""
    from .models import EvaluationResult

    evaluation = ModelEvaluation.objects.get(pk=evaluation_id)
    split = evaluation.split

    try:
        test_items = split.items.filter(group=DatasetSplitItem.Group.TEST)
        test_task_ids = list(test_items.values_list('task_id', flat=True))

        ground_truths = []
        predictions = []

        for task_id in test_task_ids:
            gt_annotation = Annotation.objects.filter(
                task_id=task_id, ground_truth=True
            ).first()

            if not gt_annotation:
                gt_annotation = Annotation.objects.filter(task_id=task_id).first()

            if gt_annotation:
                ground_truths.append(gt_annotation.result or [])
            else:
                ground_truths.append([])

            task_predictions = Prediction.objects.filter(task_id=task_id)
            if task_predictions.exists():
                predictions.append(task_predictions.first().result or [])
            else:
                predictions.append([])

        project = evaluation.project
        parsed_config = project.get_parsed_config()

        evaluator = DetectionEvaluator()
        for tag_info in parsed_config.values():
            tag_type = tag_info.get('type', '').lower()
            if tag_type in ClassificationEvaluator.get_supported_task_types():
                evaluator = ClassificationEvaluator()
                break

        results = evaluator.evaluate(
            ground_truths=ground_truths,
            predictions=predictions,
            task_ids=test_task_ids,
        )

        for model_version in evaluation.model_versions:
            EvaluationResult.objects.create(
                evaluation=evaluation,
                model_version=model_version,
                metrics=results['metrics'],
                per_class_metrics=results['per_class_metrics'],
                confusion_matrix=results['confusion_matrix'],
                error_samples=results['error_samples'],
            )

        evaluation.summary_metrics = results['metrics']
        evaluation.status = ModelEvaluation.Status.COMPLETED
        evaluation.completed_at = now()
        evaluation.save()

    except Exception as e:
        logger.exception(f'Error running evaluation: {e}')
        evaluation.status = ModelEvaluation.Status.FAILED
        evaluation.error_message = str(e)
        evaluation.save()


class StrategyViewSet(viewsets.ViewSet):
    """切割策略视图集"""

    def list(self, request):
        strategies = [
            RandomSplitStrategy,
            StratifiedSplitStrategy,
            TimeSeriesSplitStrategy,
        ]

        data = []
        for strategy_cls in strategies:
            data.append(
                {
                    'type': strategy_cls.get_strategy_type(),
                    'name': strategy_cls.get_name(),
                    'config_schema': strategy_cls.get_config_schema(),
                }
            )

        serializer = StrategySerializer(data, many=True)
        return Response(serializer.data)


class EvaluatorViewSet(viewsets.ViewSet):
    """评估器视图集"""

    def list(self, request):
        evaluators = [
            DetectionEvaluator,
            ClassificationEvaluator,
        ]

        data = []
        for evaluator_cls in evaluators:
            data.append(
                {
                    'type': evaluator_cls.get_evaluator_type(),
                    'name': evaluator_cls.get_name(),
                    'supported_task_types': evaluator_cls.get_supported_task_types(),
                    'config_schema': evaluator_cls.get_config_schema(),
                }
            )

        serializer = EvaluatorSerializer(data, many=True)
        return Response(serializer.data)
