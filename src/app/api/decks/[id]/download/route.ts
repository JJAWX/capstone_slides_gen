import { NextRequest, NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const response = await fetch(`${FASTAPI_URL}/decks/${id}/download`, {
      method: "GET",
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: "Failed to download deck", details: error },
        { status: response.status }
      );
    }

    const blob = await response.blob();
    const headers = new Headers();
    headers.set("Content-Type", "application/vnd.openxmlformats-officedocument.presentationml.presentation");
    headers.set("Content-Disposition", `attachment; filename="presentation-${id}.pptx"`);

    return new NextResponse(blob, {
      status: 200,
      headers,
    });
  } catch (error) {
    console.error("Error downloading deck:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
