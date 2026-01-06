"use client";

import { Steps, Progress, Button, Alert, Space } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import type { DeckStatus } from "@/lib/types";

interface DeckStatusProps {
  status: DeckStatus;
  progress?: number;
  currentStep?: string;
  error?: string;
  deckId?: string;
  onDownload?: () => void;
}

const statusSteps: DeckStatus[] = ["outline", "plan", "fix", "render", "done"];

const statusLabels: Record<DeckStatus, string> = {
  outline: "OUTLINE",
  plan: "PLAN",
  fix: "FIX",
  render: "RENDER",
  done: "DONE",
  error: "ERROR",
};

const statusDescriptions: Record<DeckStatus, string> = {
  outline: "Creating presentation structure",
  plan: "Planning slide content",
  fix: "Optimizing layout and text",
  render: "Generating PowerPoint file",
  done: "Presentation ready",
  error: "Generation failed",
};

export default function DeckStatus({
  status,
  progress,
  currentStep,
  error,
  deckId,
  onDownload,
}: DeckStatusProps) {
  const getCurrentStepIndex = () => {
    if (status === "error") return 0;
    return statusSteps.indexOf(status);
  };

  const currentStepIndex = getCurrentStepIndex();

  const stepItems = statusSteps.map((step, index) => ({
    title: statusLabels[step],
    description:
      index === currentStepIndex
        ? currentStep || statusDescriptions[step]
        : statusDescriptions[step],
    status:
      status === "error" && index === currentStepIndex
        ? ("error" as const)
        : index < currentStepIndex
        ? ("finish" as const)
        : index === currentStepIndex
        ? ("process" as const)
        : ("wait" as const),
  }));

  return (
    <Space orientation="vertical" size="large" style={{ width: "100%" }}>
      {error && (
        <Alert
          message="Generation Error"
          description={error}
          type="error"
          showIcon
        />
      )}

      <Steps
        current={currentStepIndex}
        items={stepItems}
        orientation="vertical"
      />

      {progress !== undefined &&
        progress > 0 &&
        status !== "done" &&
        status !== "error" && (
          <div>
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, color: "#666" }}>
                Overall Progress
              </span>
            </div>
            <Progress
              percent={Math.round(progress)}
              status="active"
              strokeColor={{
                from: "#108ee9",
                to: "#87d068",
              }}
            />
          </div>
        )}

      {status === "done" && deckId && (
        <Button
          type="primary"
          size="large"
          block
          icon={<DownloadOutlined />}
          onClick={onDownload}
        >
          Download Presentation (.pptx)
        </Button>
      )}
    </Space>
  );
}
