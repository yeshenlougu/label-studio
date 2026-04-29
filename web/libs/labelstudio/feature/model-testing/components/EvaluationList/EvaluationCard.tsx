import React from 'react';
import { Card, Tag, Typography, Space, Progress } from 'antd';
import {
  ExperimentOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { EvaluationItem } from '../../store/modelTestingStore';

const { Text, Title } = Typography;

interface EvaluationCardProps {
  evaluation: EvaluationItem;
  onClick: () => void;
}

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
  in_progress: { color: 'processing', icon: <LoadingOutlined />, text: '进行中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
};

export const EvaluationCard: React.FC<EvaluationCardProps> = ({ evaluation, onClick }) => {
  const status = statusConfig[evaluation.status as keyof typeof statusConfig] || statusConfig.pending;
  const f1Score = evaluation.summary_metrics?.f1 || 0;

  return (
    <Card hoverable onClick={onClick} style={{ cursor: 'pointer' }}>
      <div style={{ marginBottom: 12 }}>
        <Space>
          <ExperimentOutlined />
          <Title level={5} style={{ margin: 0 }}>
            {evaluation.name}
          </Title>
        </Space>
      </div>

      <Space style={{ marginBottom: 12 }}>
        <Tag color="blue">{evaluation.split_name}</Tag>
        <Tag color={status.color} icon={status.icon}>
          {status.text}
        </Tag>
      </Space>

      {evaluation.status === 'completed' && (
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">F1 分数</Text>
          <Progress
            percent={Math.round(f1Score * 100)}
            strokeColor={{
              '0%': '#ff4d4f',
              '50%': '#faad14',
              '100%': '#52c41a',
            }}
            format={(percent) => `${percent}%`}
          />
        </div>
      )}

      <div style={{ marginBottom: 8 }}>
        <Text type="secondary">模型版本: </Text>
        {evaluation.model_versions.slice(0, 2).map((version) => (
          <Tag key={version} style={{ marginBottom: 4 }}>
            {version}
          </Tag>
        ))}
        {evaluation.model_versions.length > 2 && (
          <Tag>+{evaluation.model_versions.length - 2}</Tag>
        )}
      </div>

      <Text type="secondary" style={{ fontSize: 12 }}>
        创建于 {new Date(evaluation.created_at).toLocaleString()}
      </Text>
    </Card>
  );
};
