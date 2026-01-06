import { NextRequest, NextResponse } from "next/server";
import type { DeckRequest, DeckResponse } from "@/lib/types";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8001";

/**
 * POST /api/decks
 * Creates a new deck generation task by forwarding the request to FastAPI backend.
 *
 * FastAPI Backend Responsibilities:
 * 1. OpenAI API calls for:
 *    - Outline generation (slide structure)
 *    - Content planning
 *    - Text compression/overflow handling
 * 2. Text overflow management to fit slide constraints
 * 3. PPTX file generation using python-pptx
 *
 * Request Body:
 * - prompt: string - The presentation topic
 * - slideCount: number - Number of slides to generate
 * - audience: string - Target audience (technical/business/academic/general)
 * - template: string - Template style (corporate/academic/startup/minimal)
 *
 * Response:
 * - deckId: string - Unique identifier for the deck
 * - status: string - Current generation status
 * - message?: string - Optional status message
 */
export async function POST(request: NextRequest) {
  try {
    // Parse and validate request body
    const body: DeckRequest = await request.json();

    // Validate required fields
    if (!body.prompt || !body.prompt.trim()) {
      return NextResponse.json(
        { error: "Prompt is required" },
        { status: 400 }
      );
    }

    if (!body.slideCount || body.slideCount < 5 || body.slideCount > 30) {
      return NextResponse.json(
        { error: "Slide count must be between 5 and 30" },
        { status: 400 }
      );
    }

    console.log("[POST /api/decks] Creating deck with params:", {
      prompt: body.prompt.substring(0, 50) + "...",
      slideCount: body.slideCount,
      audience: body.audience,
      template: body.template,
    });

    // Forward request to FastAPI backend
    // FastAPI will handle:
    // - OpenAI calls for outline/plan/compress
    // - Text overflow management
    // - PPTX generation
    const response = await fetch(`${FASTAPI_URL}/decks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60000), // 60 second timeout
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("[POST /api/decks] FastAPI error:", error);
      return NextResponse.json(
        {
          error: "Failed to create deck",
          details: error,
          fastapi_url: FASTAPI_URL
        },
        { status: response.status }
      );
    }

    const data: DeckResponse = await response.json();

    console.log("[POST /api/decks] Deck created successfully:", {
      deckId: data.deckId,
      status: data.status,
    });

    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        console.error("[POST /api/decks] Request timeout");
        return NextResponse.json(
          { error: "Request timeout - deck generation is taking too long" },
          { status: 504 }
        );
      }

      console.error("[POST /api/decks] Error:", error.message);
      return NextResponse.json(
        { error: "Internal server error", details: error.message },
        { status: 500 }
      );
    }

    console.error("[POST /api/decks] Unknown error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * GET /api/decks
 * Get a list of all generated decks
 */
export async function GET() {
  try {
    console.log("[GET /api/decks] Fetching decks list...");

    const response = await fetch(`${FASTAPI_URL}/decks`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("[GET /api/decks] FastAPI error:", error);
      return NextResponse.json(
        { error: "Failed to fetch decks", details: error },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log("[GET /api/decks] Fetched", data.total, "decks");

    return NextResponse.json(data);
  } catch (error) {
    console.error("[GET /api/decks] Error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
