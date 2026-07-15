<template>
  <PageContainer>
    <section class="auth-page">
      <div class="auth-copy">
        <el-tag effect="plain">CatTrace Agent 账号系统</el-tag>
        <h1>欢迎回来</h1>
        <p>管理员登录后进入全平台管理端；普通用户登录后可以上传图片识别，并只查看自己的上传记录。</p>
        <div class="role-tips">
          <span>普通用户示例：user / 任意密码</span>
          <span>管理员示例：admin / 任意密码</span>
        </div>
      </div>

      <el-form ref="formRef" class="auth-card" :model="form" :rules="rules" label-position="top">
        <h2>登录</h2>
        <el-form-item label="账号" prop="username">
          <el-input v-model="form.username" size="large" placeholder="输入 user 或 admin" />
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
import { ElMessage } from 'element-plus';
import PageContainer from '@/components/common/PageContainer.vue';
import { useUserStore } from '@/stores/user';
import type { LoginPayload } from '@/types/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = reactive<LoginPayload>({
  username: 'user',
  password: '',
});

const rules: FormRules<LoginPayload> = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

async function handleLogin() {
  await formRef.value?.validate();
  loading.value = true;

  try {
    const profile = await userStore.login(form);
    ElMessage.success(profile.role === 'admin' ? '管理员登录成功' : '用户登录成功');
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '';
    await router.push(redirect || (profile.role === 'admin' ? '/admin/dashboard' : '/recognition'));
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
