"use client";

import { Form, Input, Slider, Select, Button } from "antd";
import type { DeckRequest, Audience, Template } from "@/lib/types";

const { TextArea } = Input;

interface DeckFormProps {
  onSubmit: (request: DeckRequest) => void;
  isLoading: boolean;
}

export default function DeckForm({ onSubmit, isLoading }: DeckFormProps) {
  const [form] = Form.useForm();

  const handleFinish = (values: {
    prompt: string;
    slideCount: number;
    audience: Audience;
    template: Template;
  }) => {
    onSubmit(values);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={{
        slideCount: 10,
        audience: "business",
        template: "corporate",
      }}
      disabled={isLoading}
    >
      <Form.Item
        label="Presentation Topic"
        name="prompt"
        rules={[
          { required: true, message: "Please enter your presentation topic" },
        ]}
      >
        <TextArea
          placeholder="Enter your presentation topic (e.g., AI in Healthcare, Climate Change Solutions)"
          rows={4}
          showCount
          maxLength={500}
        />
      </Form.Item>

      <Form.Item
        label="Number of Slides"
        name="slideCount"
        tooltip="Choose between 5 and 30 slides"
      >
        <Slider min={5} max={30} marks={{ 5: "5", 15: "15", 30: "30" }} />
      </Form.Item>

      <Form.Item
        label="Target Audience"
        name="audience"
        rules={[{ required: true, message: "Please select target audience" }]}
      >
        <Select>
          <Select.Option value="technical">Technical</Select.Option>
          <Select.Option value="business">Business</Select.Option>
          <Select.Option value="academic">Academic</Select.Option>
          <Select.Option value="general">General</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        label="Template Style"
        name="template"
        rules={[{ required: true, message: "Please select template style" }]}
      >
        <Select>
          <Select.Option value="corporate">Corporate</Select.Option>
          <Select.Option value="academic">Academic</Select.Option>
          <Select.Option value="startup">Startup</Select.Option>
          <Select.Option value="minimal">Minimal</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          size="large"
          block
          loading={isLoading}
        >
          {isLoading ? "Generating..." : "Generate Slides"}
        </Button>
      </Form.Item>
    </Form>
  );
}
