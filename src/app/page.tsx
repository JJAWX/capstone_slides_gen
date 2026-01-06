"use client";

import { useState, useEffect } from "react";
import { Layout, Row, Col, Card, Typography, Space, Empty } from "antd";
import {
  FileTextOutlined,
  ThunderboltOutlined,
  BgColorsOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import DeckForm from "@/components/DeckForm";
import DeckStatus from "@/components/DeckStatus";
import DeckList from "@/components/DeckList";
import type { DeckRequest, DeckStatusResponse, DeckStatus as DeckStatusType } from "@/lib/types";

const { Content } = Layout;
const { Title, Paragraph } = Typography;

interface DeckItem {
  deckId: string;
  status: DeckStatusType;
  progress: number;
  prompt: string;
  slideCount: number;
  template: string;
  createdAt?: string;
  error?: string;
}

export default function Home() {
  const [deckId, setDeckId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusData, setStatusData] = useState<DeckStatusResponse | null>(null);
  const [decksList, setDecksList] = useState<DeckItem[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(false);

  const handleSubmit = async (request: DeckRequest) => {
    setIsLoading(true);
    setStatusData(null);

    try {
      const response = await fetch("/api/decks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error("Failed to create deck");
      }

      const data = await response.json();
      setDeckId(data.deckId);
    } catch (error) {
      console.error("Error creating deck:", error);
      setStatusData({
        deckId: "",
        status: "error",
        error: "Failed to create deck. Please try again.",
      });
      setIsLoading(false);
    }
  };

  const handleDownload = async (downloadDeckId?: string) => {
    const targetDeckId = downloadDeckId || deckId;
    if (!targetDeckId) return;

    try {
      const response = await fetch(`/api/decks/${targetDeckId}/download`);
      if (!response.ok) {
        throw new Error("Failed to download deck");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `presentation-${targetDeckId}.pptx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading deck:", error);
      alert("Failed to download deck. Please try again.");
    }
  };

  const fetchDecksList = async () => {
    setIsLoadingList(true);
    try {
      const response = await fetch("/api/decks");
      if (!response.ok) {
        throw new Error("Failed to fetch decks list");
      }

      const data = await response.json();
      setDecksList(data.decks || []);
    } catch (error) {
      console.error("Error fetching decks list:", error);
    } finally {
      setIsLoadingList(false);
    }
  };

  // Load decks list on mount
  useEffect(() => {
    fetchDecksList();
  }, []);

  // Poll status for current deck
  useEffect(() => {
    if (!deckId) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/decks/${deckId}/status`);
        if (!response.ok) {
          throw new Error("Failed to get deck status");
        }

        const data: DeckStatusResponse = await response.json();
        setStatusData(data);

        if (data.status === "done" || data.status === "error") {
          setIsLoading(false);
          clearInterval(intervalId);
          // Refresh list when deck is done
          fetchDecksList();
        }
      } catch (error) {
        console.error("Error polling status:", error);
        setStatusData({
          deckId,
          status: "error",
          error: "Failed to get status. Please refresh the page.",
        });
        setIsLoading(false);
        clearInterval(intervalId);
      }
    };

    pollStatus();
    const intervalId = setInterval(pollStatus, 2000);

    return () => {
      clearInterval(intervalId);
    };
  }, [deckId]);

  return (
    <Layout style={{ minHeight: "100vh", background: "#f0f2f5" }}>
      <Content style={{ padding: "48px 24px" }}>
        <div style={{ maxWidth: 1400, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <Title level={1}>Intelligent Slides Generator</Title>
            <Paragraph style={{ fontSize: 18, color: "#666" }}>
              Generate professional PowerPoint presentations with AI
            </Paragraph>
          </div>

          <Row gutter={[24, 24]}>
            <Col xs={24} lg={12}>
              <Card title="Create Presentation">
                <DeckForm onSubmit={handleSubmit} isLoading={isLoading} />
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Generation Status">
                {!statusData && !isLoading ? (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="Fill out the form and click 'Generate Slides' to start"
                  />
                ) : (
                  statusData && (
                    <DeckStatus
                      status={statusData.status}
                      progress={statusData.progress}
                      currentStep={statusData.currentStep}
                      error={statusData.error}
                      deckId={deckId || undefined}
                      onDownload={handleDownload}
                    />
                  )
                )}
              </Card>
            </Col>
          </Row>

          <Card title="My Presentations" style={{ marginTop: 24 }}>
            <DeckList
              decks={decksList}
              onDownload={handleDownload}
              onRefresh={fetchDecksList}
              loading={isLoadingList}
            />
          </Card>

          <Card title="Key Features" style={{ marginTop: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Space orientation="vertical" size="small">
                  <FileTextOutlined
                    style={{ fontSize: 32, color: "#1890ff" }}
                  />
                  <Title level={5}>Professional Output</Title>
                  <Paragraph type="secondary">
                    Generate clean, professional .pptx files
                  </Paragraph>
                </Space>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Space orientation="vertical" size="small">
                  <ThunderboltOutlined
                    style={{ fontSize: 32, color: "#52c41a" }}
                  />
                  <Title level={5}>Smart Layout</Title>
                  <Paragraph type="secondary">
                    Intelligently manage text length and layout constraints
                  </Paragraph>
                </Space>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Space orientation="vertical" size="small">
                  <BgColorsOutlined
                    style={{ fontSize: 32, color: "#722ed1" }}
                  />
                  <Title level={5}>Template Support</Title>
                  <Paragraph type="secondary">
                    Apply professional templates and maintain design consistency
                  </Paragraph>
                </Space>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Space orientation="vertical" size="small">
                  <AppstoreOutlined
                    style={{ fontSize: 32, color: "#fa8c16" }}
                  />
                  <Title level={5}>Multiple Slide Types</Title>
                  <Paragraph type="secondary">
                    Handle various slide types: title, content, comparison, data
                    visualization
                  </Paragraph>
                </Space>
              </Col>
            </Row>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}
