"""Views for model testing functionality."""
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from projects.models import Project
from .models import DatasetSplit
from .api import DatasetSplitViewSet
import json


class ModelTestingView(View):
    """Main view for model testing page."""

    def get(self, request, pk):
        return render(request, 'model_testing/model_testing.html', {
            'project_id': pk
        })


class ProjectListWithTestingView(View):
    """View to show project list with model testing links."""

    def get(self, request):
        projects = Project.objects.all().order_by('-created_at')
        project_list = []
        for project in projects:
            project_list.append({
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'task_count': getattr(project, 'task_number', 0),
                'annotation_count': getattr(project, 'total_annotations_number', 0),
                'created_at': project.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return render(request, 'model_testing/project_list.html', {
            'projects': project_list
        })


class SplitListView(View):
    """View to list splits for a project."""

    def get(self, request, project_id):
        splits = DatasetSplit.objects.filter(project_id=project_id).order_by('-created_at')
        data = []
        for split in splits:
            data.append({
                'id': split.id,
                'name': split.name,
                'strategy': split.strategy,
                'config': json.loads(split.config),
                'train_count': split.train_count,
                'test_count': split.test_count,
                'created_at': split.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': split.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse(data, safe=False)


class CreateSplitView(View):
    """View to create a new split."""

    def post(self, request, project_id):
        try:
            data = json.loads(request.body)
            name = data.get('name', '')
            strategy = data.get('strategy', 'random')
            config = data.get('config', {})

            if not name:
                return JsonResponse({'error': 'Name is required'}, status=400)

            viewset = DatasetSplitViewSet.as_view({'post': 'create'})
            fake_request = type('obj', (object,), {
                'method': 'POST',
                'data': {
                    'name': name,
                    'strategy': strategy,
                    'config': config,
                },
                'params': {'project_id': project_id},
                'user': request.user,
            })
            response = viewset(request, project_id=project_id)
            return JsonResponse(response.data, status=response.status_code)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class DeleteSplitView(View):
    """View to delete a split."""

    def delete(self, request, project_id, split_id):
        try:
            split = DatasetSplit.objects.get(id=split_id, project_id=project_id)
            split.delete()
            return JsonResponse({'success': True})
        except DatasetSplit.DoesNotExist:
            return JsonResponse({'error': 'Split not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
