import React from 'react';
import { Card, Row, Col, Statistic, Typography } from 'antd';
import {
  CheckCircleOutlined,
  PercentageOutlined,
  AimOutlined,
} from '@ant-design/icons';

const { Title } = Typography;

interface MetricsChartProps {
  metrics: Record<string, number>;
  perClassMetrics: Record<string, Record<string, number>>;
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ metrics, perClassMetrics }) => {
  return (
    <div>
      <Title level={5}>整体指标</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="准确率 (Accuracy)"
              value={metrics.accuracy ? (metrics.accuracy * 100).toFixed(1) : '-'}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="精确率 (Precision)"
              value={metrics.precision ? (metrics.precision * 100).toFixed(1) : '-'}
              suffix="%"
              prefix={<AimOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="召回率 (Recall)"
              value={metrics.recall ? (metrics.recall * 100).toFixed(1) : '-'}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="F1 分数"
              value={metrics.f1 ? (metrics.f1 * 100).toFixed(1) : '-'}
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {Object.keys(perClassMetrics).length > 0 && (
        <>
          <Title level={5}>分类别指标</Title>
          <Row gutter={[16, 16]}>
            {Object.entries(perClassMetrics).map(([label, classMetrics]) => (
              <Col span={6} key={label}>
                <Card size="small" title={label}>
                  <Statistic
                    title="F1"
                    value={classMetrics.f1 ? (classMetrics.f1 * 100).toFixed(1) : '-'}
                    suffix="%"
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </>
      )}
    </div>
  );
};
