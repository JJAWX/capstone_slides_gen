"use client";

import { Table, Button, Tag, Space, Typography } from "antd";
import { DownloadOutlined, ReloadOutlined } from "@ant-design/icons";
import type { DeckStatus } from "@/lib/types";

const { Text } = Typography;

interface DeckItem {
  deckId: string;
  status: DeckStatus;
  progress: number;
  prompt: string;
  slideCount: number;
  template: string;
  createdAt?: string;
  error?: string;
}

interface DeckListProps {
  decks: DeckItem[];
  onDownload: (deckId: string) => void;
  onRefresh: () => void;
  loading?: boolean;
}

const statusColors: Record<DeckStatus, string> = {
  outline: "blue",
  plan: "cyan",
  fix: "geekblue",
  render: "purple",
  done: "green",
  error: "red",
};

const statusLabels: Record<DeckStatus, string> = {
  outline: "OUTLINE",
  plan: "PLAN",
  fix: "FIX",
  render: "RENDER",
  done: "DONE",
  error: "ERROR",
};

export default function DeckList({
  decks,
  onDownload,
  onRefresh,
  loading = false,
}: DeckListProps) {
  const columns = [
    {
      title: "Topic",
      dataIndex: "prompt",
      key: "prompt",
      ellipsis: true,
      width: "30%",
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      ),
    },
    {
      title: "Slides",
      dataIndex: "slideCount",
      key: "slideCount",
      width: 80,
      align: "center" as const,
    },
    {
      title: "Template",
      dataIndex: "template",
      key: "template",
      width: 120,
      render: (template: string) => (
        <Text style={{ textTransform: "capitalize" }}>{template}</Text>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: DeckStatus) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      ),
    },
    {
      title: "Progress",
      dataIndex: "progress",
      key: "progress",
      width: 100,
      render: (progress: number, record: DeckItem) =>
        record.status === "done" ? (
          <Text type="success">100%</Text>
        ) : record.status === "error" ? (
          <Text type="danger">Failed</Text>
        ) : (
          <Text>{progress}%</Text>
        ),
    },
    {
      title: "Action",
      key: "action",
      width: 120,
      render: (_: unknown, record: DeckItem) => (
        <Space size="small">
          {record.status === "done" ? (
            <Button
              type="primary"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => onDownload(record.deckId)}
            >
              Download
            </Button>
          ) : record.status === "error" ? (
            <Text type="danger">Error</Text>
          ) : (
            <Tag color="processing">Processing...</Tag>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Text strong style={{ fontSize: 16 }}>
          Generated Presentations ({decks.length})
        </Text>
        <Button
          icon={<ReloadOutlined />}
          onClick={onRefresh}
          loading={loading}
        >
          Refresh
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={decks}
        rowKey="deckId"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `Total ${total} presentations`,
        }}
        loading={loading}
        locale={{
          emptyText: "No presentations yet. Create one to get started!",
        }}
      />
    </div>
  );
}
