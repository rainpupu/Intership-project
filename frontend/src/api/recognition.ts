import { mockResolve } from '@/api/request';
import request from '@/api/request';
import { mockAnalysis, mockCandidates } from '@/mock';
import type {
  RecognitionAnalyzeResponse,
  RecognitionAnalysis,
  RecognitionCandidate,
  RecognitionRecord,
  SubmitCampusCluePayload,
} from '@/types/recognition';

let latestAnalyzeResult: RecognitionAnalyzeResponse | null = null;

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

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

export function getRecognitionRecords(params?: { userId?: string; scope?: 'mine' | 'all' | 'clues' }): Promise<RecognitionRecord[]> {
  return request
    .get<ApiResponse<RecognitionRecord[]>, ApiResponse<RecognitionRecord[]>>('/recognition/records', {
      params: {
        scope: params?.scope ?? 'mine',
      },
    })
    .then((response) => response.data);
}

export function getPendingClueCount(): Promise<number> {
  return request
    .get<ApiResponse<{ count: number }>, ApiResponse<{ count: number }>>('/recognition/clues/pending-count')
    .then((response) => response.data.count);
}

export function submitCampusClue(
  recordId: string,
  payload: SubmitCampusCluePayload,
): Promise<RecognitionRecord> {
  return request
    .post<ApiResponse<RecognitionRecord>, ApiResponse<RecognitionRecord>>(`/recognition/records/${recordId}/submit-clue`, {
      location: payload.location,
      observed_at: payload.observedAt,
      user_remark: payload.userRemark,
    })
    .then((response) => response.data);
}

export function dismissCampusClue(recordId: string): Promise<RecognitionRecord> {
  return request
    .post<ApiResponse<RecognitionRecord>, ApiResponse<RecognitionRecord>>(`/recognition/records/${recordId}/dismiss-clue`)
    .then((response) => response.data);
}

export function confirmExistingCatForRecord(recordId: string, catId: string): Promise<{ success: boolean; catId: string }> {
  return request
    .post<ApiResponse<{ success: boolean; catId: string }>, ApiResponse<{ success: boolean; catId: string }>>(
      `/recognition/records/${recordId}/confirm-existing`,
      {
        cat_id: catId,
      },
    )
    .then((response) => response.data);
}

export function confirmExistingCat(catId: string): Promise<{ success: boolean; catId: string }> {
  const recordId = latestAnalyzeResult?.record?.id;
  if (!recordId) {
    return mockResolve({
      success: false,
      catId,
    });
  }

  return confirmExistingCatForRecord(recordId, catId);
}

export function createNewCatFromRecord(
  recordId: string,
  payload?: {
    name?: string;
    code?: string;
    description?: string;
    lastSeenLocation?: string;
  },
): Promise<{ success: boolean; catId: string; name?: string; message?: string }> {
  return request
    .post<
      ApiResponse<{ success: boolean; catId: string; name?: string; message?: string }>,
      ApiResponse<{ success: boolean; catId: string; name?: string; message?: string }>
    >(`/recognition/records/${recordId}/create-cat`, {
      name: payload?.name,
      code: payload?.code,
      description: payload?.description,
      last_seen_location: payload?.lastSeenLocation,
    })
    .then((response) => response.data);
}

export function createNewCat(payload?: {
  name?: string;
  code?: string;
  description?: string;
  lastSeenLocation?: string;
}): Promise<{ success: boolean; catId: string; name?: string; message?: string }> {
  const recordId = latestAnalyzeResult?.record?.id;
  if (!recordId) {
    return mockResolve({
      success: false,
      catId: '',
      message: '没有可创建档案的识别记录',
    });
  }

  return createNewCatFromRecord(recordId, payload);
}
