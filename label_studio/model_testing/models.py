from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DatasetSplit(models.Model):
    """数据集切割配置"""

    class SplitType(models.TextChoices):
        RANDOM = 'random', _('随机切割')
        STRATIFIED = 'stratified', _('分层切割')
        TIMESERIES = 'timeseries', _('时间序列切割')
        MANUAL = 'manual', _('手动指定')

    class Status(models.TextChoices):
        PENDING = 'pending', _('待处理')
        COMPLETED = 'completed', _('已完成')
        FAILED = 'failed', _('失败')

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='dataset_splits',
        verbose_name=_('项目'),
    )
    name = models.CharField(_('名称'), max_length=255)
    split_type = models.CharField(
        _('切割类型'),
        max_length=32,
        choices=SplitType.choices,
        default=SplitType.RANDOM,
    )
    config = models.JSONField(_('配置参数'), default=dict)
    status = models.CharField(
        _('状态'),
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('创建者'),
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    total_tasks = models.IntegerField(_('总任务数'), default=0)
    train_tasks = models.IntegerField(_('训练集任务数'), default=0)
    test_tasks = models.IntegerField(_('测试集任务数'), default=0)

    class Meta:
        db_table = 'model_testing_dataset_split'
        verbose_name = _('数据集切割')
        verbose_name_plural = _('数据集切割')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_split_type_display()})'

    def has_permission(self, user):
        user.project = self.project
        return self.project.has_permission(user)


class DatasetSplitItem(models.Model):
    """切割项 - 每个任务的分组信息"""

    class Group(models.TextChoices):
        TRAIN = 'train', _('训练集')
        TEST = 'test', _('测试集')

    split = models.ForeignKey(
        DatasetSplit,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('切割配置'),
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        related_name='split_items',
        verbose_name=_('任务'),
    )
    group = models.CharField(
        _('分组'),
        max_length=16,
        choices=Group.choices,
    )

    class Meta:
        db_table = 'model_testing_dataset_split_item'
        verbose_name = _('切割项')
        verbose_name_plural = _('切割项')
        unique_together = ['split', 'task']
        indexes = [
            models.Index(fields=['split', 'group']),
        ]

    def __str__(self):
        return f'Task {self.task_id} -> {self.get_group_display()}'


class ModelEvaluation(models.Model):
    """模型评估记录"""

    class Status(models.TextChoices):
        PENDING = 'pending', _('待处理')
        IN_PROGRESS = 'in_progress', _('进行中')
        COMPLETED = 'completed', _('已完成')
        FAILED = 'failed', _('失败')

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_('项目'),
    )
    split = models.ForeignKey(
        DatasetSplit,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_('切割配置'),
    )
    name = models.CharField(_('名称'), max_length=255)
    model_versions = models.JSONField(_('模型版本列表'), default=list)
    status = models.CharField(
        _('状态'),
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('创建者'),
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    completed_at = models.DateTimeField(_('完成时间'), null=True, blank=True)
    summary_metrics = models.JSONField(_('汇总指标'), default=dict)
    error_message = models.TextField(_('错误信息'), null=True, blank=True)

    class Meta:
        db_table = 'model_testing_model_evaluation'
        verbose_name = _('模型评估')
        verbose_name_plural = _('模型评估')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    def has_permission(self, user):
        user.project = self.project
        return self.project.has_permission(user)


class EvaluationResult(models.Model):
    """评估结果详情"""

    evaluation = models.ForeignKey(
        ModelEvaluation,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('评估记录'),
    )
    model_version = models.CharField(_('模型版本'), max_length=255)

    metrics = models.JSONField(_('整体指标'), default=dict)
    per_class_metrics = models.JSONField(_('分类别指标'), default=dict)
    confusion_matrix = models.JSONField(_('混淆矩阵'), default=list)
    error_samples = models.JSONField(_('错误样本'), default=list)

    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)

    class Meta:
        db_table = 'model_testing_evaluation_result'
        verbose_name = _('评估结果')
        verbose_name_plural = _('评估结果')
        unique_together = ['evaluation', 'model_version']

    def __str__(self):
        return f'{self.evaluation.name} - {self.model_version}'


class EvaluationReport(models.Model):
    """评估报告"""

    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        HTML = 'html', 'HTML'
        JSON = 'json', 'JSON'
        CSV = 'csv', 'CSV'

    evaluation = models.ForeignKey(
        ModelEvaluation,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('评估记录'),
    )
    format = models.CharField(
        _('格式'),
        max_length=16,
        choices=Format.choices,
    )
    file = models.FileField(
        _('文件'),
        upload_to='evaluation_reports/',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)

    class Meta:
        db_table = 'model_testing_evaluation_report'
        verbose_name = _('评估报告')
        verbose_name_plural = _('评估报告')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.evaluation.name} - {self.get_format_display()}'
