import React, { useEffect, useState } from 'react';
import { observer } from 'mobx-react-lite';
import { Modal, Form, Input, Select, message } from 'antd';
import { modelTestingStore, SplitItem, EvaluationItem } from '../store/modelTestingStore';
import { EvaluationList } from '../components/EvaluationList/EvaluationList';
import { EvaluationDetail } from '../components/EvaluationDetail/EvaluationDetail';

interface EvaluationPageProps {
  projectId: number;
  initialSplit?: SplitItem;
}

export const EvaluationPage: React.FC<EvaluationPageProps> = observer(
  ({ projectId, initialSplit }) => {
    const [selectedEvaluation, setSelectedEvaluation] = useState<EvaluationItem | null>(null);
    const [showForm, setShowForm] = useState(!!initialSplit);
    const [form] = Form.useForm();

    useEffect(() => {
      fetchEvaluations();
    }, [projectId]);

    useEffect(() => {
      if (initialSplit) {
        form.setFieldsValue({ split: initialSplit.id });
        setShowForm(true);
      }
    }, [initialSplit, form]);

    const fetchEvaluations = async () => {
      modelTestingStore.setLoading(true);
      try {
        const response = await fetch(`/api/projects/${projectId}/evaluations/`);
        const data = await response.json();
        modelTestingStore.setEvaluations(data);
      } catch (error) {
        modelTestingStore.setError('获取评估列表失败');
      }
      modelTestingStore.setLoading(false);
    };

    const handleCreateEvaluation = async (values: { name: string; split: number; model_versions: string[] }) => {
      try {
        const response = await fetch(`/api/projects/${projectId}/evaluations/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        });

        if (response.ok) {
          const newEvaluation = await response.json();
          modelTestingStore.addEvaluation(newEvaluation);
          setShowForm(false);
          message.success('评估创建成功');

          handleRunEvaluation(newEvaluation.id);
        } else {
          const error = await response.json();
          message.error(error.detail || '创建失败');
        }
      } catch (error) {
        message.error('创建评估失败');
      }
    };

    const handleRunEvaluation = async (evaluationId: number) => {
      try {
        const response = await fetch(`/api/projects/${projectId}/evaluations/${evaluationId}/run/`, {
          method: 'POST',
        });

        if (response.ok) {
          message.success('评估已开始执行');
          fetchEvaluations();
        }
      } catch (error) {
        message.error('执行评估失败');
      }
    };

    const handleExportReport = async (evaluationId: number, format: string) => {
      try {
        const response = await fetch(`/api/projects/${projectId}/evaluations/${evaluationId}/reports/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ format }),
        });

        if (response.ok) {
          message.success('报告生成中...');
        }
      } catch (error) {
        message.error('导出报告失败');
      }
    };

    if (selectedEvaluation) {
      return (
        <EvaluationDetail
          projectId={projectId}
          evaluation={selectedEvaluation}
          onBack={() => {
            setSelectedEvaluation(null);
            fetchEvaluations();
          }}
          onRerun={() => handleRunEvaluation(selectedEvaluation.id)}
          onExportReport={(format) => handleExportReport(selectedEvaluation.id, format)}
        />
      );
    }

    return (
      <>
        <EvaluationList
          projectId={projectId}
          onCreateEvaluation={() => setShowForm(true)}
          onSelectEvaluation={setSelectedEvaluation}
        />
        <Modal
          title="新建模型评估"
          open={showForm}
          onOk={() => form.submit()}
          onCancel={() => setShowForm(false)}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateEvaluation}
          >
            <Form.Item
              name="name"
              label="评估名称"
              rules={[{ required: true, message: '请输入评估名称' }]}
            >
              <Input placeholder="例如：模型A性能测试" />
            </Form.Item>

            <Form.Item
              name="split"
              label="切割配置"
              rules={[{ required: true, message: '请选择切割配置' }]}
            >
              <Select>
                {modelTestingStore.splits.map((split) => (
                  <Select.Option key={split.id} value={split.id}>
                    {split.name}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="model_versions"
              label="模型版本"
              rules={[{ required: true, message: '请选择模型版本' }]}
            >
              <Select mode="multiple" placeholder="选择要评估的模型版本">
                {}
              </Select>
            </Form.Item>
          </Form>
        </Modal>
      </>
    );
  }
);
