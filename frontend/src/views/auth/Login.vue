<template>
  <PageContainer>
    <section class="auth-page">
      <div class="auth-copy">
        <el-tag effect="plain">CatTrace Agent 账号系统</el-tag>
        <h1>欢迎回来</h1>
        <p>登录后回到首页，你可以从导航进入个人识别、猫咪图鉴或管理端。</p>
        <div class="role-tips">
          <span>普通用户：使用注册手机号登录</span>
          <span>管理员：使用总管理员创建的手机号账号登录</span>
          <span>总管理员测试：superadmin / admin123</span>
        </div>
      </div>

      <el-form ref="formRef" class="auth-card" :model="form" :rules="rules" label-position="top">
        <h2>登录</h2>
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" size="large" placeholder="请输入手机号账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button class="submit" type="primary" size="large" round :loading="loading" @click="handleLogin">
          登录
        </el-button>
        <p class="switch">
          还没有账号？
          <RouterLink to="/register">立即注册</RouterLink>
        </p>
      </el-form>
    </section>
  </PageContainer>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { FormInstance, FormRules } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { AxiosError } from 'axios';
import PageContainer from '@/components/common/PageContainer.vue';
import { useUserStore } from '@/stores/user';
import type { LoginPayload } from '@/types/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive<LoginPayload>({
  username: '',
  password: '',
});

const rules: FormRules<LoginPayload> = {
  username: [{ required: true, message: '请输入手机号账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

interface AuthErrorDetail {
  code?: string;
  message?: string;
}

function getAuthErrorDetail(error: unknown): AuthErrorDetail {
  const axiosError = error as AxiosError<{ detail?: AuthErrorDetail | string }>;
  const detail = axiosError.response?.data?.detail;
  if (typeof detail === 'object' && detail) {
    return detail;
  }

  return {
    message: typeof detail === 'string' ? detail : '登录失败，请稍后重试',
  };
}

async function handleLogin() {
  await formRef.value?.validate();
  loading.value = true;

  try {
    const profile = await userStore.login(form);
    ElMessage.success({
      message: profile.role === 'user' ? '用户登录成功' : '管理员登录成功',
      duration: 1000,
    });
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '';
    await router.push(redirect || '/');
  } catch (error) {
    const detail = getAuthErrorDetail(error);
    if (detail.code === 'PHONE_NOT_REGISTERED') {
      await ElMessageBox.alert('该手机号未注册账号，请先完成注册。', '账号不存在', {
        confirmButtonText: '去注册',
        type: 'warning',
      });
      await router.push('/register');
      return;
    }

    if (detail.code === 'INVALID_PASSWORD') {
      await ElMessageBox.alert('该手机号已经注册过，但密码不正确。请检查密码后重新输入。', '密码错误', {
        confirmButtonText: '知道了',
        type: 'error',
      });
      return;
    }

    ElMessage.error(detail.message || '登录失败，请稍后重试');
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
    radial-gradient(circle at 84% 18%, rgba(251, 207, 232, 0.42), transparent 34%),
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

.role-tips {
  display: grid;
  gap: 10px;
  margin-top: 28px;
}

.role-tips span {
  width: fit-content;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(251, 146, 60, 0.12);
  color: $color-primary-dark;
  font-weight: 800;
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
