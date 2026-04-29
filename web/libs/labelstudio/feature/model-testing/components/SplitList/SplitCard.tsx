import React from 'react';
import { Card, Tag, Typography, Progress, Space } from 'antd';
import {
  SplitCellsOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { SplitItem } from '../../store/modelTestingStore';

const { Text, Title } = Typography;

interface SplitCardProps {
  split: SplitItem;
  onClick: () => void;
}

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
};

const splitTypeNames: Record<string, string> = {
  random: '随机切割',
  stratified: '分层切割',
  timeseries: '时间序列切割',
  manual: '手动指定',
};

export const SplitCard: React.FC<SplitCardProps> = ({ split, onClick }) => {
  const status = statusConfig[split.status as keyof typeof statusConfig] || statusConfig.pending;
  const testRatio = split.total_tasks > 0 
    ? Math.round((split.test_tasks / split.total_tasks) * 100) 
    : 0;

  return (
    <Card
      hoverable
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <div style={{ marginBottom: 12 }}>
        <Space>
          <SplitCellsOutlined />
          <Title level={5} style={{ margin: 0 }}>
            {split.name}
          </Title>
        </Space>
      </div>

      <Space style={{ marginBottom: 12 }}>
        <Tag color="blue">{splitTypeNames[split.split_type] || split.split_type}</Tag>
        <Tag color={status.color} icon={status.icon}>
          {status.text}
        </Tag>
      </Space>

      <div style={{ marginBottom: 8 }}>
        <Text type="secondary">任务分布</Text>
        <Progress
          percent={100 - testRatio}
          success={{ percent: testRatio }}
          format={() => `训练: ${split.train_tasks} / 测试: ${split.test_tasks}`}
          size="small"
        />
      </div>

      <Text type="secondary" style={{ fontSize: 12 }}>
        创建于 {new Date(split.created_at).toLocaleString()}
        {split.created_by_email && ` by ${split.created_by_email}`}
      </Text>
    </Card>
  );
};
