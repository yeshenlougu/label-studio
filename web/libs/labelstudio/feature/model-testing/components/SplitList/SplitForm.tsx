import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, InputNumber, Select, Switch, Slider } from 'antd';
import { observer } from 'mobx-react-lite';
import { modelTestingStore, Strategy, ConfigField } from '../../store/modelTestingStore';

interface SplitFormProps {
  projectId: number;
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values: { name: string; split_type: string; config: Record<string, unknown> }) => void;
}

const renderField = (field: ConfigField) => {
  switch (field.type) {
    case 'number':
      return field.step ? (
        <Slider
          min={field.min}
          max={field.max}
          step={field.step}
          marks={{
            [field.min || 0]: `${field.min}`,
            [field.max || 1]: `${field.max}`,
          }}
        />
      ) : (
        <InputNumber
          min={field.min}
          max={field.max}
          step={field.step}
          style={{ width: '100%' }}
        />
      );
    case 'boolean':
      return <Switch />;
    case 'select':
      return (
        <Select>
          {field.options?.map((opt) => (
            <Select.Option key={opt.value} value={opt.value}>
              {opt.label}
            </Select.Option>
          ))}
        </Select>
      );
    default:
      return <Input />;
  }
};

export const SplitForm: React.FC<SplitFormProps> = observer(
  ({ projectId, visible, onCancel, onSubmit }) => {
    const [form] = Form.useForm();
    const { strategies } = modelTestingStore;
    const [selectedType, setSelectedType] = useState<string>('random');

    useEffect(() => {
      if (visible) {
        form.resetFields();
        setSelectedType('random');
      }
    }, [visible, form]);

    const selectedStrategy = strategies.find((s) => s.type === selectedType);

    const handleOk = async () => {
      try {
        const values = await form.validateFields();
        const config: Record<string, unknown> = {};
        
        selectedStrategy?.config_schema.fields.forEach((field) => {
          if (values[field.name] !== undefined) {
            config[field.name] = values[field.name];
          } else if (field.default !== undefined) {
            config[field.name] = field.default;
          }
        });

        onSubmit({
          name: values.name,
          split_type: selectedType,
          config,
        });
      } catch (error) {
        console.error('Form validation failed:', error);
      }
    };

    return (
      <Modal
        title="新建数据集切割"
        open={visible}
        onOk={handleOk}
        onCancel={onCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="切割名称"
            rules={[{ required: true, message: '请输入切割名称' }]}
          >
            <Input placeholder="例如：80/20 随机切割" />
          </Form.Item>

          <Form.Item label="切割策略">
            <Select value={selectedType} onChange={setSelectedType}>
              {strategies.map((strategy) => (
                <Select.Option key={strategy.type} value={strategy.type}>
                  {strategy.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {selectedStrategy?.config_schema.fields.map((field) => (
            <Form.Item
              key={field.name}
              name={field.name}
              label={field.label}
              initialValue={field.default}
              valuePropName={field.type === 'boolean' ? 'checked' : 'value'}
            >
              {renderField(field)}
            </Form.Item>
          ))}
        </Form>
      </Modal>
    );
  }
);
