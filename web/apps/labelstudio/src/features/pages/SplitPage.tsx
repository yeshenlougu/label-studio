import React, { useEffect, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { message } from 'antd';
import { modelTestingStore, SplitItem } from '../store/modelTestingStore';
import { SplitList } from '../components/SplitList/SplitList';
import { SplitDetail } from '../components/SplitDetail/SplitDetail';
import { SplitForm } from '../components/SplitList/SplitForm';

interface SplitPageProps {
  projectId: number;
  onStartEvaluation: (split: SplitItem) => void;
}

export const SplitPage: React.FC<SplitPageProps> = observer(
  ({ projectId, onStartEvaluation }) => {
    const [showForm, setShowForm] = useState(false);
    const [selectedSplit, setSelectedSplit] = useState<SplitItem | null>(null);

    useEffect(() => {
      fetchSplits();
      fetchStrategies();
    }, [projectId]);

    const fetchSplits = async () => {
      modelTestingStore.setLoading(true);
      try {
        const response = await fetch(`/api/projects/${projectId}/splits/`);
        const data = await response.json();
        modelTestingStore.setSplits(data);
      } catch (error) {
        modelTestingStore.setError('获取切割列表失败');
      }
      modelTestingStore.setLoading(false);
    };

    const fetchStrategies = async () => {
      try {
        const response = await fetch('/api/model-testing/strategies/');
        const data = await response.json();
        modelTestingStore.setStrategies(data);
      } catch (error) {
        console.error('Failed to fetch strategies:', error);
      }
    };

    const handleCreateSplit = async (values: { name: string; split_type: string; config: Record<string, unknown> }) => {
      try {
        const response = await fetch(`/api/projects/${projectId}/splits/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        });

        if (response.ok) {
          const newSplit = await response.json();
          modelTestingStore.addSplit(newSplit);
          setShowForm(false);
          message.success('切割创建成功');
        } else {
          const error = await response.json();
          message.error(error.detail || '创建失败');
        }
      } catch (error) {
        message.error('创建切割失败');
      }
    };

    const handleDeleteSplit = async (id: number) => {
      try {
        const response = await fetch(`/api/projects/${projectId}/splits/${id}/`, {
          method: 'DELETE',
        });

        if (response.ok) {
          modelTestingStore.removeSplit(id);
          message.success('删除成功');
        }
      } catch (error) {
        message.error('删除失败');
      }
    };

    if (selectedSplit) {
      return (
        <SplitDetail
          projectId={projectId}
          split={selectedSplit}
          onBack={() => setSelectedSplit(null)}
          onStartEvaluation={() => onStartEvaluation(selectedSplit)}
        />
      );
    }

    return (
      <>
        <SplitList
          projectId={projectId}
          onCreateSplit={() => setShowForm(true)}
          onSelectSplit={setSelectedSplit}
        />
        <SplitForm
          projectId={projectId}
          visible={showForm}
          onCancel={() => setShowForm(false)}
          onSubmit={handleCreateSplit}
        />
      </>
    );
  }
);
