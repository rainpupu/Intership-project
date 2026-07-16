export interface RecognitionCandidate {
  catId: string;
  name: string;
  image: string;
  cropImage?: string;
  similarity: number;
  reason: string;
  status: string;
  bbox?: number[];
}

export interface RecognitionAnalysis {
  confidence: number;
  healthHints: string[];
  behaviorHints: string[];
  summary: string;
}

export interface RecognitionAnalyzeResponse {
  candidates: RecognitionCandidate[];
  analysis: RecognitionAnalysis;
  uploadedImages: string[];
  detectedCount: number;
  elapsedMs: number;
}

export interface RecognitionRecord {
  id: string;
  userId: string;
  image: string;
  catName: string;
  similarity: number;
  location: string;
  createdAt: string;
  status: string;
}
