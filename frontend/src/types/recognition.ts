export interface RecognitionCandidate {
  catId: string;
  name: string;
  image: string;
  similarity: number;
  reason: string;
  status: string;
}

export interface RecognitionAnalysis {
  confidence: number;
  healthHints: string[];
  behaviorHints: string[];
  summary: string;
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
