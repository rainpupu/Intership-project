import { mockResolve } from '@/api/request';
import request from '@/api/request';
import { mockAnalysis, mockCandidates, mockRecognitionRecords } from '@/mock';
import type { RecognitionAnalyzeResponse, RecognitionAnalysis, RecognitionCandidate, RecognitionRecord } from '@/types/recognition';

let latestAnalyzeResult: RecognitionAnalyzeResponse | null = null;

export async function uploadEncounterImages(files: File[]): Promise<RecognitionAnalyzeResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  latestAnalyzeResult = await request.post<RecognitionAnalyzeResponse, RecognitionAnalyzeResponse>('/recognition/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 60000,
  });

  return latestAnalyzeResult;
}

export function analyzeEncounter(): Promise<RecognitionAnalysis> {
  return latestAnalyzeResult ? Promise.resolve(latestAnalyzeResult.analysis) : mockResolve(mockAnalysis);
}

export function getRecognitionCandidates(): Promise<RecognitionCandidate[]> {
  return latestAnalyzeResult ? Promise.resolve(latestAnalyzeResult.candidates) : mockResolve(mockCandidates);
}

export function getRecognitionRecords(params?: { userId?: string; scope?: 'mine' | 'all' }): Promise<RecognitionRecord[]> {
  if (params?.scope === 'mine' && params.userId) {
    return mockResolve(mockRecognitionRecords.filter((record) => record.userId === params.userId));
  }

  return mockResolve(mockRecognitionRecords);
}

export function confirmExistingCat(catId: string): Promise<{ success: boolean; catId: string }> {
  return mockResolve({
    success: true,
    catId,
  });
}

export function createNewCat(): Promise<{ success: boolean; catId: string }> {
  return mockResolve({
    success: true,
    catId: 'new-cat-mock',
  });
}
