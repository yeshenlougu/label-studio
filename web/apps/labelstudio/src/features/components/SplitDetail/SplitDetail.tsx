import React, { useEffect, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { Button, Card, Tabs, Table, Tag, Typography, Space, Spin } from 'antd';
import { ArrowLeftOutlined, ExperimentOutlined } from '@ant-design/icons';
import { modelTestingStore, SplitItem } from '../../store/modelTestingStore';

const { Title, Text } = Typography;

interface SplitDetailProps {
  projectId: number;
  split: SplitItem;
  onBack: () => void;
  onStartEvaluation: () => void;
}

export const SplitDetail: React.FC<SplitDetailProps> = observer(
  ({ projectId, split, onBack, onStartEvaluation }) => {
    const [trainTasks, setTrainTasks] = useState<unknown[]>([]);
    const [testTasks, setTestTasks] = useState<unknown[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      const fetchTasks = async () => {
        setLoading(true);
        try {
          const response = await fetch(`/api/projects/${projectId}/splits/${split.id}/tasks/`);
          const data = await response.json();
          setTrainTasks(data.tasks || []);
        } catch (error) {
          console.error('Failed to fetch tasks:', error);
        }
        setLoading(false);
      };

      fetchTasks();
    }, [projectId, split.id]);

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
          <Text ellipsis style={{ maxWidth: 300 }}>
            {JSON.stringify(data).slice(0, 100)}...
          </Text>
        ),
      },
    ];

    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>
            返回列表
          </Button>
        </div>

        <Card
          title={
            <Space>
              <Title level={4} style={{ margin: 0 }}>
                {split.name}
              </Title>
              <Tag color="blue">{split.split_type}</Tag>
            </Space>
          }
          extra={
            <Button
              type="primary"
              icon={<ExperimentOutlined />}
              onClick={onStartEvaluation}
            >
              开始模型测试
            </Button>
          }
        >
          <Space size="large">
            <div>
              <Text type="secondary">总任务数</Text>
              <Title level={3} style={{ margin: 0 }}>
                {split.total_tasks}
              </Title>
            </div>
            <div>
              <Text type="secondary">训练集</Text>
              <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                {split.train_tasks}
              </Title>
            </div>
            <div>
              <Text type="secondary">测试集</Text>
              <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                {split.test_tasks}
              </Title>
            </div>
          </Space>
        </Card>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
            <Spin size="large" />
          </div>
        ) : (
          <Card style={{ marginTop: 16 }}>
            <Tabs
              items={[
                {
                  key: 'train',
                  label: `训练集 (${split.train_tasks})`,
                  children: (
                    <Table
                      dataSource={trainTasks}
                      columns={columns}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      size="small"
                    />
                  ),
                },
                {
                  key: 'test',
                  label: `测试集 (${split.test_tasks})`,
                  children: (
                    <Table
                      dataSource={testTasks}
                      columns={columns}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      size="small"
                    />
                  ),
                },
              ]}
            />
          </Card>
        )}
      </div>
    );
  }
);
