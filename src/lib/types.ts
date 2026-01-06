export type DeckStatus = 
  | "outline" 
  | "analyze" 
  | "content" 
  | "optimize" 
  | "layout" 
  | "review" 
  | "done" 
  | "error";

export type Audience = "technical" | "business" | "academic" | "general";
export type Template = 
  | "corporate" 
  | "academic" 
  | "startup" 
  | "minimal" 
  | "creative" 
  | "nature" 
  | "futuristic" 
  | "luxury";

export interface DeckRequest {
  prompt: string;
  slideCount: number;
  audience: Audience;
  template: Template;
}

export interface DeckResponse {
  deckId: string;
  status: DeckStatus;
  message?: string;
}

export interface DeckStatusResponse {
  deckId: string;
  status: DeckStatus;
  progress?: number;
  currentStep?: string;
  error?: string;
}

export interface DeckDownloadResponse {
  url: string;
  filename: string;
}
