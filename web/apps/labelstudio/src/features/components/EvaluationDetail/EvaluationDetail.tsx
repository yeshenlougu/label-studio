import React from 'react';
import { observer } from 'mobx-react-lite';
import { Button, Card, Tabs, Typography, Space, Spin, Descriptions, Tag } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { modelTestingStore, EvaluationItem } from '../../store/modelTestingStore';
import { MetricsChart } from './MetricsChart';
import { ConfusionMatrix } from './ConfusionMatrix';
import { ErrorSamples } from './ErrorSamples';

const { Title, Text } = Typography;

interface EvaluationDetailProps {
  projectId: number;
  evaluation: EvaluationItem;
  onBack: () => void;
  onRerun: () => void;
  onExportReport: (format: string) => void;
}

export const EvaluationDetail: React.FC<EvaluationDetailProps> = observer(
  ({ projectId, evaluation, onBack, onRerun, onExportReport }) => {
    const result = evaluation.results?.[0];

    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
              返回列表
            </Button>
            <Button icon={<ReloadOutlined />} onClick={onRerun}>
              重新评估
            </Button>
            <Button icon={<DownloadOutlined />} onClick={() => onExportReport('json')}>
              导出报告
            </Button>
          </Space>
        </div>

        <Card
          title={
            <Title level={4} style={{ margin: 0 }}>
              {evaluation.name}
            </Title>
          }
        >
          <Descriptions column={4}>
            <Descriptions.Item label="切割配置">{evaluation.split_name}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={evaluation.status === 'completed' ? 'success' : 'default'}>
                {evaluation.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(evaluation.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="创建者">{evaluation.created_by_email}</Descriptions.Item>
          </Descriptions>
        </Card>

        {evaluation.status === 'in_progress' && (
          <Card style={{ marginTop: 16 }}>
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" />
              <Text style={{ display: 'block', marginTop: 16 }}>评估进行中...</Text>
            </div>
          </Card>
        )}

        {evaluation.status === 'completed' && result && (
          <Card style={{ marginTop: 16 }}>
            <Tabs
              items={[
                {
                  key: 'metrics',
                  label: '评估指标',
                  children: <MetricsChart metrics={result.metrics} perClassMetrics={result.per_class_metrics} />,
                },
                {
                  key: 'confusion',
                  label: '混淆矩阵',
                  children: <ConfusionMatrix data={result.confusion_matrix} />,
                },
                {
                  key: 'errors',
                  label: `错误样本 (${result.error_samples?.length || 0})`,
                  children: <ErrorSamples taskIds={result.error_samples || []} projectId={projectId} />,
                },
              ]}
            />
          </Card>
        )}
      </div>
    );
  }
);
