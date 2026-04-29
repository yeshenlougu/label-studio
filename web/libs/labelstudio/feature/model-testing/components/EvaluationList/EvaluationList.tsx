import React from 'react';
import { observer } from 'mobx-react-lite';
import { Button, Card, Empty, Spin, Typography, Space } from 'antd';
import { PlusOutlined, ExperimentOutlined } from '@ant-design/icons';
import { modelTestingStore, EvaluationItem } from '../../store/modelTestingStore';
import { EvaluationCard } from './EvaluationCard';

const { Title } = Typography;

interface EvaluationListProps {
  projectId: number;
  onCreateEvaluation: () => void;
  onSelectEvaluation: (evaluation: EvaluationItem) => void;
}

export const EvaluationList: React.FC<EvaluationListProps> = observer(
  ({ projectId, onCreateEvaluation, onSelectEvaluation }) => {
    const { evaluations, loading } = modelTestingStore;

    if (loading) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      );
    }

    return (
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <Title level={4} style={{ margin: 0 }}>
            <ExperimentOutlined style={{ marginRight: 8 }} />
            模型评估
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreateEvaluation}>
            新建评估
          </Button>
        </div>

        {evaluations.length === 0 ? (
          <Empty
            description="暂无评估记录"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={onCreateEvaluation}>
              创建第一个评估
            </Button>
          </Empty>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 16 }}>
            {evaluations.map((evaluation) => (
              <EvaluationCard
                key={evaluation.id}
                evaluation={evaluation}
                onClick={() => onSelectEvaluation(evaluation)}
              />
            ))}
          </div>
        )}
      </div>
    );
  }
);
