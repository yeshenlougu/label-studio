import React, { useEffect, useState } from 'react';
import { Table, Typography, Empty, Spin, Button } from 'antd';
import { LinkOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface ErrorSamplesProps {
  projectId: number;
  taskIds: number[];
}

export const ErrorSamples: React.FC<ErrorSamplesProps> = ({ projectId, taskIds }) => {
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState<unknown[]>([]);

  useEffect(() => {
    if (taskIds.length === 0) return;

    const fetchTasks = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/projects/${projectId}/tasks/?ids=${taskIds.slice(0, 50).join(',')}`);
        const data = await response.json();
        setTasks(data);
      } catch (error) {
        console.error('Failed to fetch error samples:', error);
      }
      setLoading(false);
    };

    fetchTasks();
  }, [projectId, taskIds]);

  if (taskIds.length === 0) {
    return <Empty description="没有错误样本" />;
  }

  if (loading) {
    return <Spin />;
  }

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
    },
    {
      title: '数据预览',
      dataIndex: 'data',
      key: 'data',
      render: (data: Record<string, unknown>) => (
        <Text ellipsis style={{ maxWidth: 400 }}>
          {JSON.stringify(data).slice(0, 200)}...
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: { id: number }) => (
        <Button
          type="link"
          icon={<LinkOutlined />}
          href={`/projects/${projectId}/data?task=${record.id}`}
          target="_blank"
        >
          查看
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={5}>错误样本 ({taskIds.length})</Title>
      <Text type="secondary">以下任务的预测结果与人工标注不匹配</Text>
      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        size="small"
        style={{ marginTop: 16 }}
      />
    </div>
  );
};
