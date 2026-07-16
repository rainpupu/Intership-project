<template>
  <PageContainer>
    <button class="back-button" type="button" aria-label="返回上一页" @click="goBack">
      ←
    </button>

    <section class="profile-head">
      <div>
        <h1 class="page-title">个人信息</h1>
        <p class="page-subtitle">维护账号头像和基础资料。当前为前端 Mock 保存，后续可直接替换为 FastAPI 用户资料接口。</p>
      </div>
      <el-tag size="large" effect="plain">{{ roleLabel }}</el-tag>
    </section>

    <section v-if="userStore.profile" class="profile-grid">
      <aside class="profile-card soft-card">
        <div class="avatar-wrap">
          <img :src="form.avatar" :alt="form.nickname" @error="useDefaultAvatar" />
          <span>{{ roleLabel }}</span>
        </div>
        <h2>{{ userStore.displayName }}</h2>
        <p>{{ form.bio || '还没有填写个人简介。' }}</p>

        <el-upload class="avatar-upload" :auto-upload="false" :show-file-list="false" accept="image/*" :on-change="handleAvatarFile">
          <el-button round>选择本地头像</el-button>
        </el-upload>
      </aside>

      <el-form ref="formRef" class="form-card soft-card" :model="form" :rules="rules" label-position="top">
        <div class="form-section">
          <h2 class="section-title">基础资料</h2>
          <div class="form-grid">
            <el-form-item label="账号">
              <el-input :model-value="userStore.profile.username" disabled size="large" />
            </el-form-item>
            <el-form-item label="角色">
              <el-input :model-value="roleLabel" disabled size="large" />
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="form.nickname" size="large" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="身份说明" prop="campusRole">
              <el-input v-model="form.campusRole" size="large" placeholder="例如：东门志愿者 / 管理员" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" size="large" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" size="large" placeholder="请输入手机号" />
            </el-form-item>
          </div>
        </div>

        <div class="form-section">
          <h2 class="section-title">头像与简介</h2>
          <el-form-item label="头像 URL" prop="avatar">
            <el-input v-model="form.avatar" size="large" placeholder="可粘贴图片 URL，或选择本地头像生成预览" />
          </el-form-item>
          <el-form-item label="个人简介" prop="bio">
            <el-input
              v-model="form.bio"
              type="textarea"
              :rows="5"
              maxlength="160"
              show-word-limit
              placeholder="介绍你的猫咪守护身份、关注区域或领养偏好"
            />
          </el-form-item>
        </div>

        <div class="actions">
          <el-button round @click="resetForm">重置</el-button>
          <el-button type="primary" round :loading="saving" @click="saveProfile">保存资料</el-button>
        </div>
      </el-form>
    </section>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { FormInstance, FormRules, UploadFile } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import PageContainer from '@/components/common/PageContainer.vue';
import { useAppStore } from '@/stores/app';
import { useUserStore } from '@/stores/user';
import type { UpdateProfilePayload } from '@/types/user';

const userStore = useUserStore();
const appStore = useAppStore();
const router = useRouter();
const formRef = ref<FormInstance>();
const saving = ref(false);

const form = reactive<UpdateProfilePayload>({
  nickname: '',
  avatar: '',
  email: '',
  phone: '',
  campusRole: '',
  bio: '',
});
const defaultAvatar = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=200&q=80';

const roleLabel = computed(() => (userStore.isAdmin ? '管理员' : '普通用户'));

const rules: FormRules<UpdateProfilePayload> = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  avatar: [
    { required: true, message: '请设置头像', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value.startsWith('http') || value.startsWith('data:image/')) {
          callback();
          return;
        }

        callback(new Error('头像需为图片 URL 或本地图片预览'));
      },
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '请输入有效邮箱', trigger: 'blur' }],
};

function syncFormFromStore() {
  if (!userStore.profile) {
    return;
  }

  Object.assign(form, {
    nickname: userStore.profile.nickname,
    avatar: userStore.profile.avatar,
    email: userStore.profile.email,
    phone: userStore.profile.phone,
    campusRole: userStore.profile.campusRole,
    bio: userStore.profile.bio,
  });
}

function handleAvatarFile(file: UploadFile) {
  const rawFile = file.raw;

  if (!rawFile) {
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    form.avatar = String(reader.result || form.avatar);
  };
  reader.readAsDataURL(rawFile);
}

function useDefaultAvatar() {
  form.avatar = defaultAvatar;
}

async function resetForm() {
  try {
    await ElMessageBox.confirm('确定放弃当前修改并恢复上次保存的资料吗？', '重置资料', {
      confirmButtonText: '确认重置',
      cancelButtonText: '取消',
      type: 'warning',
    });
    syncFormFromStore();
  } catch {
    // 用户取消重置时不需要反馈。
  }
}

async function goBack() {
  await router.push(appStore.profileReturnPath || '/');
}

async function saveProfile() {
  await formRef.value?.validate();
  saving.value = true;

  try {
    await userStore.updateProfile({ ...form });
    ElMessage.success('个人信息已更新');
  } finally {
    saving.value = false;
  }
}

syncFormFromStore();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.back-button {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  margin-bottom: 18px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.86);
  color: $color-text;
  cursor: pointer;
  font-size: 24px;
  font-weight: 800;
  box-shadow: 0 12px 28px rgba(180, 104, 48, 0.12);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 16px 36px rgba(180, 104, 48, 0.18);
    transform: translateX(-2px);
  }
}

.profile-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.profile-grid {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.profile-card,
.form-card {
  padding: 24px;
}

.profile-card {
  position: sticky;
  top: 96px;
  text-align: center;
}

.avatar-wrap {
  position: relative;
  width: 148px;
  height: 148px;
  margin: 0 auto 18px;
}

.avatar-wrap img {
  width: 148px;
  height: 148px;
  border: 6px solid #fff;
  border-radius: 42px;
  box-shadow: 0 18px 42px rgba(180, 104, 48, 0.18);
  object-fit: cover;
}

.avatar-wrap span {
  position: absolute;
  right: -8px;
  bottom: 8px;
  padding: 7px 11px;
  border-radius: 999px;
  background: $color-primary;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.profile-card h2 {
  margin: 0 0 8px;
  color: $color-text;
}

.profile-card p {
  margin: 0 0 20px;
  color: $color-text-secondary;
  line-height: 1.7;
}

.avatar-upload {
  display: flex;
  justify-content: center;
}

.form-section + .form-section {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid rgba(251, 146, 60, 0.16);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 18px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
}

@media (max-width: 900px) {
  .profile-head,
  .actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .profile-card {
    position: static;
  }
}
</style>
