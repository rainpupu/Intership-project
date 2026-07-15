import { mockAnalysis, mockCandidates, mockRecognitionRecords } from '@/api/mock';
import type { RecognitionAnalysis, RecognitionCandidate, RecognitionRecord } from '@/types/recognition';

export function uploadEncounterImages(files: File[]): Promise<{ uploaded: number; taskId: string }> {
  return Promise.resolve({
    uploaded: files.length,
    taskId: 'mock-recognition-task',
  });
}

export function analyzeEncounter(): Promise<RecognitionAnalysis> {
  return Promise.resolve(mockAnalysis);
}

export function getRecognitionCandidates(): Promise<RecognitionCandidate[]> {
  return Promise.resolve(mockCandidates);
}

export function getRecognitionRecords(params?: { userId?: string; scope?: 'mine' | 'all' }): Promise<RecognitionRecord[]> {
  if (params?.scope === 'mine' && params.userId) {
    return Promise.resolve(mockRecognitionRecords.filter((record) => record.userId === params.userId));
  }

  return Promise.resolve(mockRecognitionRecords);
}

export function confirmExistingCat(catId: string): Promise<{ success: boolean; catId: string }> {
  return Promise.resolve({
    success: true,
    catId,
  });
}

export function createNewCat(): Promise<{ success: boolean; catId: string }> {
  return Promise.resolve({
    success: true,
    catId: 'new-cat-mock',
  });
}
