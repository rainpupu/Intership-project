import { mockResolve } from '@/api/request';
import { mockCats, mockObservations } from '@/mock';
import type {
  Cat,
  Observation,
  AuditRecord,
  BatchMarkPayload,
  BatchAuditPayload,
  AuditStats,
  OperationResult,
} from '@/types/cat';

// ==================== 有状态 Mock 数据层 ====================
// 所有写入操作直接修改这块内存数据，调用 getCatList 即可看到最新状态。
// 后续对接后端时，只需将下面各函数体替换为 axios/fetch 调用即可，不改接口签名。

/** 模拟网络延迟（毫秒），设为 0 可关闭延迟 */
const MOCK_DELAY = 300;

/** 猫咪列表（可变副本） */
let _cats: Cat[] = structuredClone(mockCats);

/** 审核记录池（可变） */
const _auditRecords: AuditRecord[] = [];

/** 标记记录：catId -> { markType, remark } */
const _marks: Record<string, { markType: string; remark: string }> = {};

// ==================== 种子数据：模拟历史审核记录 ====================
// 确保首次打开页面时，点击"审核记录"就能看到内容，而非空表格。
function _seedAuditRecords() {
  const baseTime = Date.now();
  const seed: AuditRecord[] = [
    { id: 'seed-1', catId: 'cat-orange',  action: '审核通过',   remark: '档案完整，照片清晰', operator: '管理员A', operatedAt: new Date(baseTime - 2 * 86400000).toISOString() },
    { id: 'seed-2', catId: 'cat-orange',  action: '标记待复查', remark: '食欲不稳定需持续观察', operator: '管理员B', operatedAt: new Date(baseTime - 5 * 86400000).toISOString() },
    { id: 'seed-3', catId: 'cat-milk',    action: '审核通过',   remark: '健康检查已完成',       operator: '管理员A', operatedAt: new Date(baseTime - 1 * 86400000).toISOString() },
    { id: 'seed-4', catId: 'cat-black',   action: '审核驳回',   remark: '照片不清晰需重新提交',   operator: '管理员C', operatedAt: new Date(baseTime - 3 * 86400000).toISOString() },
    { id: 'seed-5', catId: 'cat-black',   action: '审核通过',   remark: '补充照片后审核通过',    operator: '管理员A', operatedAt: new Date(baseTime - 1 * 86400000).toISOString() },
    { id: 'seed-6', catId: 'cat-sanhua',  action: '审核通过',   remark: '已领养，归档处理',       operator: '管理员B', operatedAt: new Date(baseTime - 10 * 86400000).toISOString() },
    { id: 'seed-7', catId: 'cat-tabby',   action: '标记待复查', remark: '右眼分泌物需安排复查',    operator: '管理员C', operatedAt: new Date(baseTime - 4 * 86400000).toISOString() },
    { id: 'seed-8', catId: 'cat-white',   action: '审核通过',   remark: '基础健康检查完成',       operator: '管理员A', operatedAt: new Date(baseTime - 6 * 86400000).toISOString() },
  ];
  _auditRecords.push(...seed);

  // 给已有"需复查/观察中"的猫咪预置标记
  _marks['cat-tabby'] = { markType: '重点观察', remark: '右眼分泌物需复查' };
  _marks['cat-milk']  = { markType: '常规标记', remark: '食欲监控中' };
}
_seedAuditRecords();

/** ID 自增计数器 */
let _nextId = 100;

/** 重置模拟数据（可在浏览器控制台调用以恢复初始状态） */
;(window as any).__resetCatMock = () => {
  _cats = structuredClone(mockCats);
  _auditRecords.length = 0;
  Object.keys(_marks).forEach((k) => delete _marks[k]);
  _nextId = 100;
  _seedAuditRecords();
  console.log('[Mock] 猫咪数据已重置为初始状态（含种子审核记录）');
};

// ==================== 猫咪基本信息 ====================

export async function getCatList(): Promise<Cat[]> {
  await delay();
  // 将标记信息合入返回数据（Cat 类型未扩展 markType 字段，这里通过类型断言临时补齐）
  return _cats.map((cat) => {
    const mark = _marks[cat.id];
    return mark ? { ...cat, _markType: mark.markType, _markRemark: mark.remark } as Cat : cat;
  });
}

export async function getCatDetail(id: string): Promise<Cat | undefined> {
  await delay();
  return _cats.find((cat) => cat.id === id);
}

export async function getCatObservations(id: string): Promise<Observation[]> {
  await delay();
  return mockObservations.filter((item) => item.catId === id);
}

// ==================== 审核记录 ====================

export async function getCatAuditRecords(catId: string): Promise<AuditRecord[]> {
  await delay();
  return _auditRecords
    .filter((r) => r.catId === catId)
    .sort((a, b) => new Date(b.operatedAt).getTime() - new Date(a.operatedAt).getTime());
}

export async function getAuditStats(): Promise<AuditStats> {
  await delay();
  const approved = _auditRecords.filter((r) => r.action === '审核通过').length;
  const rejected = _auditRecords.filter((r) => r.action === '审核驳回').length;
  return {
    total: _auditRecords.length,
    pending: Math.max(0, _cats.length - approved - rejected),
    approved,
    rejected,
  };
}

// ==================== 审核操作 ====================

export async function approveCat(catId: string, remark?: string): Promise<OperationResult> {
  await delay();
  const cat = _cats.find((c) => c.id === catId);
  if (!cat) return { success: false, message: '猫咪不存在' };

  _auditRecords.push({
    id: String(_nextId++),
    catId,
    action: '审核通过',
    remark: remark || '审核通过',
    operator: '当前管理员',
    operatedAt: new Date().toISOString(),
  });

  // 审核通过后清除标记
  if (_marks[catId]) {
    delete _marks[catId];
  }

  console.log(`[Mock] 审核通过: ${cat.name} (${catId}), 备注: ${remark || '-'}`);
  return { success: true, message: `「${cat.name}」审核通过` };
}

export async function rejectCat(catId: string, reason: string): Promise<OperationResult> {
  await delay();
  const cat = _cats.find((c) => c.id === catId);
  if (!cat) return { success: false, message: '猫咪不存在' };

  _auditRecords.push({
    id: String(_nextId++),
    catId,
    action: '审核驳回',
    remark: reason,
    operator: '当前管理员',
    operatedAt: new Date().toISOString(),
  });

  console.log(`[Mock] 审核驳回: ${cat.name} (${catId}), 原因: ${reason}`);
  return { success: true, message: `「${cat.name}」已驳回` };
}

export async function batchApproveCats(payload: BatchAuditPayload): Promise<OperationResult> {
  await delay();
  const now = new Date().toISOString();
  let count = 0;

  for (const catId of payload.catIds) {
    const cat = _cats.find((c) => c.id === catId);
    if (!cat) continue;

    _auditRecords.push({
      id: String(_nextId++),
      catId,
      action: '审核通过',
      remark: payload.remark || '批量审核通过',
      operator: '当前管理员',
      operatedAt: now,
    });

    if (_marks[catId]) delete _marks[catId];
    count++;
  }

  console.log(`[Mock] 批量审核通过: ${count} 条记录`);
  return { success: true, message: `已批量审核通过 ${count} 条记录` };
}

export async function batchRejectCats(payload: BatchAuditPayload): Promise<OperationResult> {
  await delay();
  const now = new Date().toISOString();
  let count = 0;

  for (const catId of payload.catIds) {
    const cat = _cats.find((c) => c.id === catId);
    if (!cat) continue;

    _auditRecords.push({
      id: String(_nextId++),
      catId,
      action: '审核驳回',
      remark: payload.remark || '批量驳回',
      operator: '当前管理员',
      operatedAt: now,
    });
    count++;
  }

  console.log(`[Mock] 批量驳回: ${count} 条记录`);
  return { success: true, message: `已批量驳回 ${count} 条记录` };
}

// ==================== 批量标记 ====================

export async function batchMarkCats(payload: BatchMarkPayload): Promise<OperationResult> {
  await delay();
  const now = new Date().toISOString();
  let count = 0;

  for (const catId of payload.catIds) {
    const cat = _cats.find((c) => c.id === catId);
    if (!cat) continue;

    _marks[catId] = { markType: payload.markType, remark: payload.remark ?? '' };

    _auditRecords.push({
      id: String(_nextId++),
      catId,
      action: '标记待复查',
      remark: `[${payload.markType}] ${payload.remark ?? ''}`,
      operator: '当前管理员',
      operatedAt: now,
    });
    count++;
  }

  console.log(`[Mock] 批量标记: ${count} 只猫咪, 类型: ${payload.markType}`);
  return { success: true, message: `已批量标记 ${count} 只猫咪` };
}

export async function batchUnmarkCats(catIds: string[]): Promise<OperationResult> {
  await delay();
  const now = new Date().toISOString();
  let count = 0;

  for (const catId of catIds) {
    if (_marks[catId]) {
      delete _marks[catId];
      _auditRecords.push({
        id: String(_nextId++),
        catId,
        action: '已归档',
        remark: '取消标记',
        operator: '当前管理员',
        operatedAt: now,
      });
      count++;
    }
  }

  console.log(`[Mock] 取消标记: ${count} 只猫咪`);
  return { success: true, message: `已取消 ${count} 只猫咪的标记` };
}

// ==================== 关注操作 ====================

export async function toggleCatFocus(catId: string, isFocus: boolean): Promise<OperationResult> {
  await delay();
  const cat = _cats.find((c) => c.id === catId);
  if (!cat) return { success: false, message: '猫咪不存在' };

  cat.isFocus = isFocus;
  console.log(`[Mock] 关注状态变更: ${cat.name} -> ${isFocus ? '已关注' : '未关注'}`);
  return { success: true, message: isFocus ? `「${cat.name}」已设为关注` : `「${cat.name}」已取消关注` };
}

export async function batchToggleFocus(catIds: string[], isFocus: boolean): Promise<OperationResult> {
  await delay();
  let count = 0;

  for (const catId of catIds) {
    const cat = _cats.find((c) => c.id === catId);
    if (cat) {
      cat.isFocus = isFocus;
      count++;
    }
  }

  console.log(`[Mock] 批量关注: ${count} 只猫咪 -> ${isFocus ? '已关注' : '未关注'}`);
  return { success: true, message: isFocus ? `已关注 ${count} 只猫咪` : `已取消关注 ${count} 只猫咪` };
}

// ==================== 档案操作 ====================

export async function createCat(catData: Omit<Cat, 'id'>): Promise<OperationResult & { id?: string }> {
  await delay();
  const newId = `cat-new-${_nextId++}`;
  const newCat: Cat = { id: newId, ...catData };
  _cats.push(newCat);

  console.log(`[Mock] 新增猫咪: ${newCat.name} (${newId})`);
  return { success: true, message: `「${newCat.name}」档案创建成功`, id: newId };
}

export async function updateCat(catId: string, catData: Partial<Cat>): Promise<OperationResult> {
  await delay();
  const idx = _cats.findIndex((c) => c.id === catId);
  if (idx === -1) return { success: false, message: '猫咪不存在' };

  _cats[idx] = { ..._cats[idx], ...catData };
  console.log(`[Mock] 更新档案: ${_cats[idx].name} (${catId})`);
  return { success: true, message: `「${_cats[idx].name}」档案更新成功` };
}

export async function deleteCat(catId: string): Promise<OperationResult> {
  await delay();
  const idx = _cats.findIndex((c) => c.id === catId);
  if (idx === -1) return { success: false, message: '猫咪不存在' };

  const name = _cats[idx].name;
  _cats.splice(idx, 1);

  // 清理关联数据
  delete _marks[catId];

  console.log(`[Mock] 删除档案: ${name} (${catId})`);
  return { success: true, message: `「${name}」档案已删除` };
}

// ==================== 工具函数 ====================

/** 模拟网络延迟 */
function delay(ms: number = MOCK_DELAY): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
