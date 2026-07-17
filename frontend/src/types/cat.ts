export type AdoptionStatus = '待领养' | '已领养' | '云领养中' | '暂不开放';

// 猫咪记录
export interface Cat {
  id: string;
  code: string;
  name: string;
  coverImage: string;
  galleryImages: string[];
  coatColor: string;
  ageStage: string;
  gender: string;
  personalityTags: string[];
  healthStatus: string;
  moodStatus: string;
  adoptionStatus: AdoptionStatus;
  lastSeenLocation: string;
  lastSeenAt: string;
  description: string;
  isFocus: boolean;
}

// 猫咪观察记录
export interface Observation {
  id: string;
  catId: string;
  location: string;
  moodStatus: string;
  healthStatus: string;
  observedAt: string;
  description: string;
}

// 审核记录
export interface AuditRecord {
  id: string;
  catId: string;
  action: '审核通过' | '审核驳回' | '标记待复查' | '已归档';
  remark: string;
  operator: string;        // 操作人
  operatedAt: string;      // ISO 时间
}

// 批量标记参数
export interface BatchMarkPayload {
  catIds: string[];
  markType: '重点观察' | '待回访' | '已处理';
  remark?: string;
}

// 批量审核参数
export interface BatchAuditPayload {
  catIds: string[];
  remark?: string;
}

// 审核统计
export interface AuditStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
}

// 通用操作结果
export interface OperationResult {
  success: boolean;
  message?: string;
}