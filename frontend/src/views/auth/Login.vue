<template>
  <PageContainer>
    <section class="auth-page">
      <div class="auth-visual" aria-label="CatTrace Agent">
        <div class="visual-content">
          <span class="brand-badge">CatTrace Agent</span>
          <h1>守护校园里的<span>每一次相遇</span></h1>
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

function resolveLoginRedirect(role: string, redirect: string) {
  if (role === 'admin' || role === 'super_admin') {
    return redirect.startsWith('/admin') ? redirect : '/admin/dashboard';
  }

  return redirect && !redirect.startsWith('/admin') ? redirect : '/';
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
    await router.push(resolveLoginRedirect(profile.role, redirect));
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

.auth-visual {
  @include card-shell(30px);
  position: relative;
  display: flex;
  align-items: flex-end;
  min-height: 420px;
  overflow: hidden;
  padding: 0;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.04) 0%, rgba(15, 23, 42, 0.62) 100%),
    url('https://images.unsplash.com/photo-1574158622682-e40e69881006?auto=format&fit=crop&w=1400&q=85') center / cover;
}

.visual-content {
  position: relative;
  z-index: 1;
  max-width: 560px;
  padding: 42px;
  color: #fff;
}

.brand-badge {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(12px);
  font-size: 13px;
  font-weight: 800;
}

.visual-content h1 {
  max-width: 680px;
  margin: 0;
  font-size: 46px;
  line-height: 1.12;
  letter-spacing: 0;
}

.visual-content h1 span {
  display: block;
  padding: 0;
  border: 0;
  background: transparent;
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

  .auth-visual {
    min-height: 320px;
  }
}

@media (max-width: 560px) {
  .visual-content {
    padding: 28px;
  }

  .visual-content h1 {
    font-size: 34px;
  }
}
</style>
