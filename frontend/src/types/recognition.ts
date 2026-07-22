export interface RecognitionCandidate {
  catId: string;
  name: string;
  image: string;
  cropImage?: string;
  matchedImage?: string;
  similarity: number;
  reason: string;
  status: string;
  bbox?: number[];
  modelType?: 'breed' | 'individual' | 'new';
  breedName?: string;
  breedConfidence?: number;
  healthStatus?: string;
  healthConfidence?: number;
  moodStatus?: string;
  moodConfidence?: number;
  identityStatus?: string;
  bestIdentityMatch?: {
    catId: string;
    name: string;
    image: string;
    similarity: number;
  } | null;
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
  record?: RecognitionRecord;
}

export interface RecognitionRecord {
  id: string;
  userId: string;
  image: string;
  catId?: string | null;
  catName: string;
  similarity: number;
  modelType?: 'breed' | 'individual' | 'new';
  breedName?: string;
  breedConfidence?: number;
  identityStatus?: string;
  bestIdentityMatch?: {
    catId: string;
    name: string;
    image: string;
    similarity: number;
  } | null;
  healthStatus?: string;
  moodStatus?: string;
  location: string;
  observedAt?: string;
  userRemark?: string;
  createdAt: string;
  status: string;
}

export interface SubmitCampusCluePayload {
  location: string;
  observedAt?: string;
  userRemark?: string;
}

export interface ConfirmExistingCatPayload {
  location: string;
  observedAt: string;
}
