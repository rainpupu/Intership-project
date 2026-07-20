<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">账号管理</h1>
        <p class="page-subtitle">总管理员可查看所有用户和管理员，并创建新的管理员手机号账号。</p>
      </div>
      <el-button type="primary" round @click="dialogVisible = true">注册新管理员</el-button>
    </section>

    <section class="soft-card table-card">
      <div class="toolbar">
        <el-segmented v-model="query.role" :options="roleOptions" @change="fetchUsers" />
        <el-input
          v-model="query.keyword"
          class="search"
          clearable
          placeholder="搜索手机号、昵称或邮箱"
          @clear="fetchUsers"
          @keyup.enter="fetchUsers"
        />
        <el-button round @click="fetchUsers">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="users" row-key="id">
        <el-table-column prop="phone" label="手机号账号" min-width="140" />
        <el-table-column prop="nickname" label="昵称" min-width="130" />
        <el-table-column prop="email" label="邮箱" min-width="190" />
        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="row.role === 'user' ? 'info' : row.role === 'admin' ? 'warning' : 'danger'">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="campusRole" label="职责说明" min-width="150" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.role === 'user'"
              size="small"
              round
              @click="changeRole(row, 'admin')"
            >
              设为管理员
            </el-button>
            <el-button
              v-else-if="row.role === 'admin'"
              size="small"
              round
              @click="changeRole(row, 'user')"
            >
              设为普通用户
            </el-button>
            <span v-else class="muted">总管理员不可变更</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="dialogVisible" title="注册新管理员" width="520px">
      <el-form ref="adminFormRef" :model="adminForm" :rules="adminRules" label-position="top">
        <el-form-item label="手机号账号" prop="phone">
          <el-input v-model="adminForm.phone" maxlength="11" placeholder="请输入管理员手机号" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="adminForm.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="adminForm.nickname" placeholder="例如：东区管理员" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="adminForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="管理员职责" prop="campusRole">
          <el-select v-model="adminForm.campusRole" placeholder="请选择管理员职责">
            <el-option
              v-for="option in adminRoleOptions"
              :key="option"
              :label="option"
              :value="option"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button round @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" round :loading="creating" @click="submitAdmin">创建管理员</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import { createAdmin, getUserList, updateUserRole } from '@/api/auth';
import { getRequestErrorMessage } from '@/api/request';
import type { CreateAdminPayload, UserListQuery, UserProfile, UserRole } from '@/types/user';

const users = ref<UserProfile[]>([]);
const loading = ref(false);
const creating = ref(false);
const dialogVisible = ref(false);
const adminFormRef = ref<FormInstance>();

const roleOptions = [
  { label: '全部', value: 'all' },
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '总管理员', value: 'super_admin' },
];
const adminRoleOptions = ['平台管理员', '审核管理员', '猫咪档案管理员'];

const query = reactive<UserListQuery>({
  role: 'all',
  keyword: '',
});

const adminForm = reactive<CreateAdminPayload>({
  phone: '',
  password: '',
  nickname: '',
  email: '',
  campusRole: '平台管理员',
});

const adminRules: FormRules<CreateAdminPayload> = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的 11 位手机号', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱', trigger: 'blur' },
  ],
  campusRole: [{ required: true, message: '请输入管理员职责', trigger: 'blur' }],
};

function roleLabel(role: UserRole) {
  if (role === 'super_admin') return '总管理员';
  if (role === 'admin') return '管理员';
  if (role === 'user') return '普通用户';
  return '访客';
}

async function fetchUsers() {
  loading.value = true;
  try {
    users.value = await getUserList({ ...query });
  } catch (error) {
    users.value = [];
    ElMessage.error(getRequestErrorMessage(error, '获取账号列表失败'));
  } finally {
    loading.value = false;
  }
}

async function submitAdmin() {
  await adminFormRef.value?.validate();
  creating.value = true;
  try {
    await createAdmin({ ...adminForm });
    ElMessage.success('管理员账号已创建');
    dialogVisible.value = false;
    Object.assign(adminForm, {
      phone: '',
      password: '',
      nickname: '',
      email: '',
      campusRole: '平台管理员',
    });
    await fetchUsers();
  } catch (error) {
    ElMessage.error(getRequestErrorMessage(error, '创建管理员失败'));
  } finally {
    creating.value = false;
  }
}

async function changeRole(user: UserProfile, role: Extract<UserRole, 'user' | 'admin'>) {
  const targetLabel = role === 'admin' ? '管理员' : '普通用户';
  await ElMessageBox.confirm(`确定将 ${user.nickname || user.phone} 设置为${targetLabel}吗？`, '调整角色', {
    type: 'warning',
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  });
  try {
    await updateUserRole({
      userId: user.id,
      role,
    });
  } catch (error) {
    ElMessage.error(getRequestErrorMessage(error, '角色更新失败'));
    return;
  }
  ElMessage.success('角色已更新');
  await fetchUsers();
}

onMounted(fetchUsers);
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head,
.toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.table-card {
  overflow: hidden;
  padding: 18px;
}

.search {
  max-width: 320px;
}

.muted {
  color: $color-text-secondary;
  font-size: 13px;
}

@media (max-width: 900px) {
  .page-head,
  .toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .search {
    max-width: none;
    width: 100%;
  }
}
</style>
