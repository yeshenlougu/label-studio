import React from 'react';
import { observer } from 'mobx-react-lite';
import { Button, Card, Empty, Spin, Typography } from 'antd';
import { PlusOutlined, SplitCellsOutlined } from '@ant-design/icons';
import { modelTestingStore, SplitItem } from '../../store/modelTestingStore';
import { SplitCard } from './SplitCard';

const { Title } = Typography;

interface SplitListProps {
  projectId: number;
  onCreateSplit: () => void;
  onSelectSplit: (split: SplitItem) => void;
}

export const SplitList: React.FC<SplitListProps> = observer(
  ({ projectId, onCreateSplit, onSelectSplit }) => {
    const { splits, loading } = modelTestingStore;

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
            <SplitCellsOutlined style={{ marginRight: 8 }} />
            数据集切割
          </Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreateSplit}>
            新建切割
          </Button>
        </div>

        {splits.length === 0 ? (
          <Empty
            description="暂无切割配置"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={onCreateSplit}>
              创建第一个切割
            </Button>
          </Empty>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {splits.map((split) => (
              <SplitCard
                key={split.id}
                split={split}
                onClick={() => onSelectSplit(split)}
              />
            ))}
          </div>
        )}
      </div>
    );
  }
);
