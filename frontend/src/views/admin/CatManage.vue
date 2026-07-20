<template>
  <main class="admin-page">
    <!-- 页面头部 -->
    <section class="page-head">
      <div>
        <h1 class="page-title">猫咪管理</h1>
        <p class="page-subtitle">管理猫咪档案，进行批量标记与标记管理，查看审核记录。</p>
      </div>
      <el-button type="primary" round @click="handleAddCat">新增猫咪档案</el-button>
    </section>

    <!-- 批量操作工具栏 -->
    <section class="toolbar">
      <el-button
        round
        plain
        :disabled="selectedCats.length === 0"
        @click="handleBatchMark"
      >
        批量标记
      </el-button>
      <el-button
        round
        plain
        :disabled="selectedCats.length === 0"
        @click="handleBatchUnmark"
      >
        批量取消标记
      </el-button>
      <el-button
        round
        plain
        :disabled="selectedCats.length === 0"
        @click="handleBatchFocus"
      >
        批量关注
      </el-button>
      <el-button
        round
        plain
        :disabled="selectedCats.length === 0"
        @click="handleBatchUnfocus"
      >
        批量取消关注
      </el-button>
      <span v-if="selectedCats.length > 0" class="selected-tip">
        已选 {{ selectedCats.length }} 项
      </span>
    </section>

    <!-- 表格 -->
    <section class="soft-card table-card">
      <el-table
        :data="cats"
        row-key="id"
        @selection-change="handleSelectionChange"
        v-loading="listLoading"
      >
        <!-- 多选列 -->
        <el-table-column type="selection" width="55" />

        <el-table-column label="猫咪" min-width="200">
          <template #default="{ row }">
            <div class="cat-cell">
              <img :src="row.coverImage" :alt="row.name" />
              <div>
                <strong>{{ row.name }}</strong>
                <p>{{ row.code }}</p>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="coatColor" label="毛色" width="100" />
        <el-table-column prop="ageStage" label="年龄阶段" width="100" />
        <el-table-column prop="healthStatus" label="健康状态" width="120" />
        <el-table-column prop="adoptionStatus" label="领养状态" width="120" />
        <el-table-column prop="lastSeenLocation" label="最近出现地点" min-width="160" />

        <!-- 标记状态列 -->
        <el-table-column label="标记" width="120">
          <template #default="{ row }">
            <el-tag
              v-if="catMarkMap[row.id]"
              size="small"
              :type="markTagType(catMarkMap[row.id].markType)"
              effect="light"
            >
              {{ catMarkMap[row.id].markType }}
            </el-tag>
            <span v-else class="cell-dim">—</span>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="text" size="small" @click="handleViewAudit(row)">
              审核记录
            </el-button>
            <el-button type="text" size="small" @click="handleToggleFocus(row)">
              {{ row.isFocus ? '取消关注' : '关注' }}
            </el-button>
            <el-button type="text" size="small" class="danger-action" @click="handleDeleteCat(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 新增猫咪档案 -->
    <el-dialog v-model="catDialogVisible" title="新增猫咪档案" width="640px">
      <el-form :model="catForm" label-width="96px">
        <el-form-item label="编号" required>
          <el-input v-model="catForm.code" placeholder="例如 CT-2026-0001" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="catForm.name" placeholder="例如 橘子" />
        </el-form-item>
        <el-form-item label="封面图">
          <el-input v-model="catForm.coverImage" placeholder="图片 URL，可后续补充" />
        </el-form-item>
        <el-form-item label="毛色">
          <el-input v-model="catForm.coatColor" placeholder="例如 橘白、狸花、三花" />
        </el-form-item>
        <el-form-item label="年龄阶段">
          <el-select v-model="catForm.ageStage" placeholder="请选择">
            <el-option label="幼猫" value="幼猫" />
            <el-option label="成年" value="成年" />
            <el-option label="老年" value="老年" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="catForm.gender" placeholder="请选择">
            <el-option label="公" value="公" />
            <el-option label="母" value="母" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="健康状态">
          <el-input v-model="catForm.healthStatus" placeholder="例如 健康良好、观察中、需复查" />
        </el-form-item>
        <el-form-item label="领养状态">
          <el-select v-model="catForm.adoptionStatus" placeholder="请选择">
            <el-option label="待领养" value="待领养" />
            <el-option label="已领养" value="已领养" />
            <el-option label="云领养中" value="云领养中" />
            <el-option label="暂不开放" value="暂不开放" />
          </el-select>
        </el-form-item>
        <el-form-item label="最近地点">
          <el-input v-model="catForm.lastSeenLocation" placeholder="例如 三号楼花坛" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="catForm.description" type="textarea" :rows="3" placeholder="补充性格、健康、活动范围等信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="catDialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="catSubmitting" @click="handleCreateCat">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审核记录弹窗 -->
    <el-dialog v-model="auditDialogVisible" :title="`审核记录 — ${currentAuditCatName}`" width="580px">
      <el-table :data="auditRecords" v-loading="auditLoading" empty-text="暂无审核记录">
        <el-table-column prop="action" label="操作">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="auditActionTag(row.action)"
              effect="light"
            >
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="operatedAt" label="操作时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.operatedAt) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button round @click="auditDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRequestErrorMessage } from '@/api/request'
import {
  getCatList,
  getCatAuditRecords,
  batchMarkCats,
  batchUnmarkCats,
  toggleCatFocus,
  batchToggleFocus,
  createCat,
  deleteCat,
} from '@/api/cat'
import type { Cat, AuditRecord, BatchMarkPayload } from '@/types/cat'

// ========== 数据 ==========
const cats = ref<Cat[]>([])
const selectedCats = ref<Cat[]>([])
const listLoading = ref(false)
const catDialogVisible = ref(false)
const catSubmitting = ref(false)

// 标记映射（从 getCatList 返回的 _markType/_markRemark 中提取）
const catMarkMap = ref<Record<string, { markType: string; remark: string }>>({})

const DEFAULT_CAT_IMAGE = 'https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=900&q=80'

const catForm = reactive<Omit<Cat, 'id'>>({
  code: '',
  name: '',
  coverImage: '',
  galleryImages: [],
  coatColor: '',
  ageStage: '成年',
  gender: '未知',
  personalityTags: [],
  healthStatus: '观察中',
  moodStatus: '稳定',
  adoptionStatus: '暂不开放',
  lastSeenLocation: '',
  lastSeenAt: new Date().toISOString(),
  description: '',
  isFocus: false,
})

// 审核记录弹窗
const auditDialogVisible = ref(false)
const auditRecords = ref<AuditRecord[]>([])
const auditLoading = ref(false)
const currentAuditCatId = ref<string>('')
const currentAuditCatName = ref<string>('')

// ========== 工具函数 ==========

/** 刷新猫咪列表 */
const refreshCatList = async () => {
  listLoading.value = true
  try {
    const data = await getCatList()
    cats.value = data

    // 从 getCatList 返回数据中提取标记信息（mock 层注入 _markType / _markRemark 字段）
    const markMap: Record<string, { markType: string; remark: string }> = {}
    data.forEach((cat: any) => {
      if (cat._markType) {
        markMap[cat.id] = { markType: cat._markType, remark: cat._markRemark || '' }
      }
    })
    catMarkMap.value = markMap

    selectedCats.value = []
  } catch (error) {
    cats.value = []
    ElMessage.error(getRequestErrorMessage(error, '获取猫咪列表失败'))
  } finally {
    listLoading.value = false
  }
}

/** 获取选中猫咪ID列表 */
const getSelectedCatIds = (): string[] => selectedCats.value.map((c) => c.id)

/** 标记 tag 类型映射 */
const markTagType = (markType: string) => {
  const map: Record<string, string> = { '重点观察': 'danger', '健康异常': 'warning', '行为异常': 'warning', '常规标记': 'info' }
  return map[markType] || 'info'
}

/** 审核动作 tag 类型映射 */
const auditActionTag = (action: string) => {
  const map: Record<string, string> = { '审核通过': 'success', '审核驳回': 'danger', '标记待复查': 'warning', '已归档': 'info' }
  return map[action] || 'info'
}

/** 格式化时间（ISO -> 本地可读格式） */
const formatTime = (iso: string) => {
  if (!iso) return '—'
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ========== 生命周期 ==========
onMounted(() => {
  refreshCatList()
})

// ========== 表格选中事件 ==========
const handleSelectionChange = (selection: Cat[]) => {
  selectedCats.value = selection
}

// ========== 功能处理函数 ==========

// 新增档案
const handleAddCat = () => {
  resetCatForm()
  catDialogVisible.value = true
}

const resetCatForm = () => {
  Object.assign(catForm, {
    code: `CT-${new Date().getFullYear()}-${Date.now().toString().slice(-6)}`,
    name: '',
    coverImage: '',
    galleryImages: [],
    coatColor: '',
    ageStage: '成年',
    gender: '未知',
    personalityTags: [],
    healthStatus: '观察中',
    moodStatus: '稳定',
    adoptionStatus: '暂不开放',
    lastSeenLocation: '',
    lastSeenAt: new Date().toISOString(),
    description: '',
    isFocus: false,
  })
}

const handleCreateCat = async () => {
  if (!catForm.code.trim() || !catForm.name.trim()) {
    ElMessage.warning('请填写编号和名称')
    return
  }

  catSubmitting.value = true
  try {
    const payload: Omit<Cat, 'id'> = {
      ...catForm,
      code: catForm.code.trim(),
      name: catForm.name.trim(),
      coverImage: catForm.coverImage.trim() || DEFAULT_CAT_IMAGE,
      galleryImages: catForm.coverImage.trim() ? [catForm.coverImage.trim()] : [DEFAULT_CAT_IMAGE],
      coatColor: catForm.coatColor.trim() || '未知',
      healthStatus: catForm.healthStatus.trim() || '观察中',
      lastSeenLocation: catForm.lastSeenLocation.trim() || '未知地点',
      description: catForm.description.trim() || '管理员新增的猫咪档案。',
    }
    const result = await createCat(payload)
    ElMessage.success(result.message ?? '猫咪档案创建成功')
    catDialogVisible.value = false
    await refreshCatList()
  } catch (error) {
    ElMessage.error(getRequestErrorMessage(error, '新增猫咪档案失败'))
  } finally {
    catSubmitting.value = false
  }
}

// 批量标记
const handleBatchMark = async () => {
  try {
    const { value } = await ElMessageBox.prompt(
      '请输入批量标记内容（如"重点观察"）',
      '批量标记',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '标记内容不能为空',
      },
    )
    const payload: BatchMarkPayload = {
      catIds: getSelectedCatIds(),
      markType: '重点观察',
      remark: value,
    }
    const result = await batchMarkCats(payload)
    ElMessage.success(result.message ?? `已成功标记 ${payload.catIds.length} 只猫咪`)
    await refreshCatList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量标记失败')
    }
  }
}

// 批量取消标记
const handleBatchUnmark = async () => {
  try {
    await ElMessageBox.confirm(
      `确认取消选中 ${selectedCats.value.length} 只猫咪的标记？`,
      '批量取消标记',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    const catIds = getSelectedCatIds()
    await batchUnmarkCats(catIds)
    ElMessage.success(`已取消 ${catIds.length} 只猫咪的标记`)
    await refreshCatList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量取消标记失败')
    }
  }
}

// 查看审核记录
const handleViewAudit = async (row: Cat) => {
  currentAuditCatId.value = row.id
  currentAuditCatName.value = row.name
  auditDialogVisible.value = true
  auditLoading.value = true
  try {
    auditRecords.value = await getCatAuditRecords(row.id)
  } catch {
    ElMessage.error('获取审核记录失败')
  } finally {
    auditLoading.value = false
  }
}

// 切换关注状态
const handleToggleFocus = async (row: Cat) => {
  try {
    const newFocus = !row.isFocus
    await toggleCatFocus(row.id, newFocus)

    // 替换整个数组元素以强制 Vue 响应式触发 DOM 更新
    const idx = cats.value.findIndex((c) => c.id === row.id)
    if (idx !== -1) {
      cats.value[idx] = { ...cats.value[idx], isFocus: newFocus }
    }

    ElMessage.success(newFocus ? '已设为关注' : '已取消关注')
  } catch {
    ElMessage.error('操作失败')
  }
}

const handleDeleteCat = async (row: Cat) => {
  try {
    await ElMessageBox.confirm(
      `确认删除「${row.name}」的猫咪档案？删除后相关观察记录和审核记录也会被移除。`,
      '删除猫咪档案',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    const result = await deleteCat(row.id)
    ElMessage.success(result.message ?? `「${row.name}」档案已删除`)
    await refreshCatList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(getRequestErrorMessage(error, '删除猫咪档案失败'))
    }
  }
}

// 批量关注
const handleBatchFocus = async () => {
  try {
    await ElMessageBox.confirm(
      `确认关注选中的 ${selectedCats.value.length} 只猫咪？`,
      '批量关注',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    const catIds = getSelectedCatIds()
    const result = await batchToggleFocus(catIds, true)
    ElMessage.success(result.message ?? `已关注 ${catIds.length} 只猫咪`)
    await refreshCatList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量关注失败')
    }
  }
}

// 批量取消关注
const handleBatchUnfocus = async () => {
  try {
    await ElMessageBox.confirm(
      `确认取消关注选中的 ${selectedCats.value.length} 只猫咪？`,
      '批量取消关注',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    const catIds = getSelectedCatIds()
    const result = await batchToggleFocus(catIds, false)
    ElMessage.success(result.message ?? `已取消关注 ${catIds.length} 只猫咪`)
    await refreshCatList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量取消关注失败')
    }
  }
}
</script>

<style scoped lang="scss">
.admin-page {
  padding: 28px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;

  .selected-tip {
    color: $color-text-secondary;
    font-size: 13px;
    margin-left: 8px;
  }
}

.table-card {
  overflow: hidden;
  padding: 8px;
}

.cat-cell {
  display: flex;
  align-items: center;
  gap: 12px;

  img {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    object-fit: cover;
  }

  strong {
    color: $color-text;
  }

  p {
    margin: 4px 0 0;
    color: $color-text-secondary;
    font-size: 12px;
  }
}

.cell-dim {
  color: $color-text-secondary;
  font-size: 13px;
}

.danger-action {
  color: #d93025;
}
</style>
