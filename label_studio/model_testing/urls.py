from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import DatasetSplitViewSet, EvaluatorViewSet, ModelEvaluationViewSet, StrategyViewSet

router = DefaultRouter()
router.register(r'strategies', StrategyViewSet, basename='strategy')
router.register(r'evaluators', EvaluatorViewSet, basename='evaluator')

urlpatterns = [
    path('', include(router.urls)),
]

project_router = DefaultRouter()
project_router.register(r'splits', DatasetSplitViewSet, basename='project-split')
project_router.register(r'evaluations', ModelEvaluationViewSet, basename='project-evaluation')

project_urlpatterns = [
    path('', include(project_router.urls)),
]
