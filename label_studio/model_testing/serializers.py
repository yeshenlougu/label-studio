from rest_framework import serializers

from .models import DatasetSplit, DatasetSplitItem, EvaluationReport, ModelEvaluation


class DatasetSplitItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetSplitItem
        fields = ['id', 'task', 'group', 'split']
        read_only_fields = ['id', 'split']


class DatasetSplitSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = DatasetSplit
        fields = [
            'id',
            'project',
            'name',
            'split_type',
            'config',
            'status',
            'created_by',
            'created_by_email',
            'created_at',
            'updated_at',
            'total_tasks',
            'train_tasks',
            'test_tasks',
            'items_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'status']

    def get_items_count(self, obj):
        return obj.items.count()

    def get_created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return None


class DatasetSplitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetSplit
        fields = ['name', 'split_type', 'config']


class DatasetSplitDetailSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()
    train_task_ids = serializers.SerializerMethodField()
    test_task_ids = serializers.SerializerMethodField()

    class Meta:
        model = DatasetSplit
        fields = [
            'id',
            'project',
            'name',
            'split_type',
            'config',
            'status',
            'created_by',
            'created_by_email',
            'created_at',
            'updated_at',
            'total_tasks',
            'train_tasks',
            'test_tasks',
            'items_count',
            'train_task_ids',
            'test_task_ids',
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return None

    def get_train_task_ids(self, obj):
        return list(obj.items.filter(group='train').values_list('task_id', flat=True))

    def get_test_task_ids(self, obj):
        return list(obj.items.filter(group='test').values_list('task_id', flat=True))


class EvaluationResultSerializer(serializers.Serializer):
    model_version = serializers.CharField()
    metrics = serializers.JSONField()
    per_class_metrics = serializers.JSONField()
    confusion_matrix = serializers.JSONField()
    error_samples = serializers.JSONField()


class ModelEvaluationSerializer(serializers.ModelSerializer):
    results = EvaluationResultSerializer(many=True, read_only=True)
    split_name = serializers.SerializerMethodField()
    created_by_email = serializers.SerializerMethodField()

    class Meta:
        model = ModelEvaluation
        fields = [
            'id',
            'project',
            'split',
            'split_name',
            'name',
            'model_versions',
            'status',
            'created_by',
            'created_by_email',
            'created_at',
            'completed_at',
            'summary_metrics',
            'error_message',
            'results',
        ]
        read_only_fields = ['id', 'created_at', 'completed_at', 'created_by', 'status', 'summary_metrics']

    def get_split_name(self, obj):
        if obj.split:
            return obj.split.name
        return None

    def get_created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return None


class ModelEvaluationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelEvaluation
        fields = ['name', 'split', 'model_versions']


class EvaluationReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationReport
        fields = ['id', 'evaluation', 'format', 'file', 'created_at']
        read_only_fields = ['id', 'created_at', 'file']


class StrategyConfigFieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    label = serializers.CharField()
    default = serializers.CharField(allow_null=True, required=False)
    min = serializers.FloatField(allow_null=True, required=False)
    max = serializers.FloatField(allow_null=True, required=False)
    step = serializers.FloatField(allow_null=True, required=False)
    options = serializers.ListField(allow_null=True, required=False)
    description = serializers.CharField(allow_null=True, required=False)


class StrategySerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField()
    config_schema = serializers.DictField()


class EvaluatorSerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField()
    supported_task_types = serializers.ListField()
    config_schema = serializers.DictField()
