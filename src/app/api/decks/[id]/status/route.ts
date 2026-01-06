import { NextRequest, NextResponse } from "next/server";
import type { DeckStatusResponse } from "@/lib/types";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8001";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const response = await fetch(`${FASTAPI_URL}/decks/${id}/status`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: "Failed to get deck status", details: error },
        { status: response.status }
      );
    }

    const data: DeckStatusResponse = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error getting deck status:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
