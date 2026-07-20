import request from '@/api/request';
import type {
  Cat,
  Observation,
  AuditRecord,
  BatchMarkPayload,
  BatchAuditPayload,
  AuditStats,
  OperationResult,
} from '@/types/cat';

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

function unwrapResult(response: ApiResponse<OperationResult>): OperationResult {
  return response.data ?? { success: response.code === 200, message: response.message };
}

export async function getCatList(params?: {
  keyword?: string;
  adoptionStatus?: string;
  isFocus?: boolean;
}): Promise<Cat[]> {
  const response = await request.get<ApiResponse<Cat[]>, ApiResponse<Cat[]>>('/cats', {
    params: {
      keyword: params?.keyword,
      adoption_status: params?.adoptionStatus,
      is_focus: params?.isFocus,
    },
  });
  return response.data;
}

export async function getCatDetail(id: string): Promise<Cat | undefined> {
  const response = await request.get<ApiResponse<Cat>, ApiResponse<Cat>>(`/cats/${id}`);
  return response.data;
}

export async function getCatObservations(id: string): Promise<Observation[]> {
  const response = await request.get<ApiResponse<Observation[]>, ApiResponse<Observation[]>>(`/cats/${id}/observations`);
  return response.data;
}

export async function getCatAuditRecords(catId: string): Promise<AuditRecord[]> {
  const response = await request.get<ApiResponse<AuditRecord[]>, ApiResponse<AuditRecord[]>>(`/cats/${catId}/audit-records`);
  return response.data;
}

export async function getAuditStats(): Promise<AuditStats> {
  const cats = await getCatList();
  const approved = cats.filter((cat) => !cat.isFocus && cat.healthStatus !== '需复查').length;
  const rejected = 0;
  return {
    total: cats.length,
    pending: Math.max(0, cats.length - approved - rejected),
    approved,
    rejected,
  };
}

export async function approveCat(catId: string, remark?: string): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-unmark', {
    catIds: [catId],
    remark,
  });
  return unwrapResult(response);
}

export async function rejectCat(catId: string, reason: string): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-mark', {
    catIds: [catId],
    markType: '待回访',
    remark: reason,
  });
  return unwrapResult(response);
}

export async function batchApproveCats(payload: BatchAuditPayload): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-unmark', {
    catIds: payload.catIds,
    remark: payload.remark,
  });
  return unwrapResult(response);
}

export async function batchRejectCats(payload: BatchAuditPayload): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-mark', {
    catIds: payload.catIds,
    markType: '待回访',
    remark: payload.remark,
  });
  return unwrapResult(response);
}

export async function batchMarkCats(payload: BatchMarkPayload): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-mark', payload);
  return unwrapResult(response);
}

export async function batchUnmarkCats(catIds: string[]): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-unmark', { catIds });
  return unwrapResult(response);
}

export async function toggleCatFocus(catId: string, isFocus: boolean): Promise<OperationResult> {
  const response = await request.put<ApiResponse<OperationResult>, ApiResponse<OperationResult>>(`/cats/${catId}/focus`, {
    isFocus,
  });
  return unwrapResult(response);
}

export async function batchToggleFocus(catIds: string[], isFocus: boolean): Promise<OperationResult> {
  const response = await request.post<ApiResponse<OperationResult>, ApiResponse<OperationResult>>('/cats/batch-focus', {
    catIds,
    isFocus,
  });
  return unwrapResult(response);
}

export async function createCat(catData: Omit<Cat, 'id'>): Promise<OperationResult & { id?: string }> {
  const response = await request.post<ApiResponse<Cat>, ApiResponse<Cat>>('/cats', catData);
  return {
    success: true,
    message: `「${response.data.name}」档案创建成功`,
    id: response.data.id,
  };
}

export async function updateCat(catId: string, catData: Partial<Cat>): Promise<OperationResult> {
  const response = await request.put<ApiResponse<Cat>, ApiResponse<Cat>>(`/cats/${catId}`, catData);
  return {
    success: true,
    message: `「${response.data.name}」档案更新成功`,
  };
}

export async function deleteCat(catId: string): Promise<OperationResult> {
  const response = await request.delete<ApiResponse<OperationResult>, ApiResponse<OperationResult>>(`/cats/${catId}`);
  return unwrapResult(response);
}
