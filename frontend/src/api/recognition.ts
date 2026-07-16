import { mockResolve } from '@/api/request';
import { mockAnalysis, mockCandidates, mockRecognitionRecords } from '@/mock';
import type { RecognitionAnalysis, RecognitionCandidate, RecognitionRecord } from '@/types/recognition';

export function uploadEncounterImages(files: File[]): Promise<{ uploaded: number; taskId: string }> {
  return mockResolve({
    uploaded: files.length,
    taskId: 'mock-recognition-task',
  });
}

export function analyzeEncounter(): Promise<RecognitionAnalysis> {
  return mockResolve(mockAnalysis);
}

export function getRecognitionCandidates(): Promise<RecognitionCandidate[]> {
  return mockResolve(mockCandidates);
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
