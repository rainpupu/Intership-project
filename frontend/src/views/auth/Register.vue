<template>
  <PageContainer>
    <section class="auth-page">
      <div class="auth-copy">
        <el-tag effect="plain">普通用户注册</el-tag>
        <h1>加入校园守护</h1>
        <p>注册后可上传猫咪图片进行识别，后续后端接入后会按账号隔离个人上传记录和识别历史。</p>
      </div>

      <el-form ref="formRef" class="auth-card" :model="form" :rules="rules" label-position="top">
        <h2>创建账号</h2>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" size="large" placeholder="例如：东门志愿者" />
        </el-form-item>
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" size="large" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-button class="submit" type="primary" size="large" round :loading="loading" @click="handleRegister">
          注册并登录
        </el-button>
        <p class="switch">
          已有账号？
          <RouterLink to="/login">去登录</RouterLink>
        </p>
      </el-form>
    </section>
  </PageContainer>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage } from 'element-plus';
import PageContainer from '@/components/common/PageContainer.vue';
import { useUserStore } from '@/stores/user';
import type { RegisterPayload } from '@/types/user';

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive<RegisterPayload>({
  username: '',
  password: '',
  nickname: '',
});

const rules: FormRules<RegisterPayload> = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
};

async function handleRegister() {
  await formRef.value?.validate();
  loading.value = true;

  try {
    await userStore.register(form);
    ElMessage.success('注册成功，已进入个人识别中心');
    await router.push('/recognition');
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.auth-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 28px;
  align-items: center;
  min-height: calc(100vh - 180px);
}

.auth-copy {
  @include card-shell(30px);
  min-height: 420px;
  padding: 48px;
  background:
    radial-gradient(circle at 84% 18%, rgba(96, 165, 250, 0.24), transparent 34%),
    rgba(255, 255, 255, 0.78);
}

.auth-copy h1 {
  margin: 24px 0 12px;
  color: $color-text;
  font-size: 54px;
  letter-spacing: 0;
}

.auth-copy p {
  max-width: 560px;
  margin: 0;
  color: $color-text-secondary;
  font-size: 17px;
  line-height: 1.8;
}

.auth-card {
  @include card-shell(26px);
  padding: 28px;
}

.auth-card h2 {
  margin: 0 0 22px;
  color: $color-text;
  font-size: 30px;
}

.submit {
  width: 100%;
}

.switch {
  margin: 18px 0 0;
  color: $color-text-secondary;
  text-align: center;
}

.switch a {
  color: $color-primary-dark;
  font-weight: 800;
}

@media (max-width: 900px) {
  .auth-page {
    grid-template-columns: 1fr;
  }
}
</style>
