import React from 'react';
import { Table, Typography, Empty } from 'antd';

const { Title } = Typography;

interface ConfusionMatrixProps {
  data: {
    labels: string[];
    matrix: number[][];
  };
}

export const ConfusionMatrix: React.FC<ConfusionMatrixProps> = ({ data }) => {
  if (!data || !data.labels || data.labels.length === 0) {
    return <Empty description="无混淆矩阵数据" />;
  }

  const { labels, matrix } = data;

  const columns = [
    {
      title: '实际 \\ 预测',
      dataIndex: 'label',
      key: 'label',
      fixed: 'left' as const,
      width: 100,
    },
    ...labels.map((label, index) => ({
      title: label,
      dataIndex: `col_${index}`,
      key: `col_${index}`,
      width: 80,
      render: (value: number) => {
        const intensity = value / Math.max(...matrix.flat(), 1);
        const bgColor = `rgba(24, 144, 255, ${intensity})`;
        return (
          <div
            style={{
              backgroundColor: bgColor,
              padding: '4px 8px',
              borderRadius: 4,
              textAlign: 'center',
              color: intensity > 0.5 ? '#fff' : '#000',
            }}
          >
            {value}
          </div>
        );
      },
    })),
  ];

  const dataSource = labels.map((label, rowIndex) => {
    const row: Record<string, unknown> = { label, key: rowIndex };
    matrix[rowIndex]?.forEach((value, colIndex) => {
      row[`col_${colIndex}`] = value;
    });
    return row;
  });

  return (
    <div>
      <Title level={5}>混淆矩阵</Title>
      <Table
        dataSource={dataSource}
        columns={columns}
        pagination={false}
        size="small"
        scroll={{ x: 'max-content' }}
      />
    </div>
  );
};
