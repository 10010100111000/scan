import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      // 前端直接请求后端地址（通过 VITE_GLOB_API_URL），不再依赖本地代理或额外反向代理服务
    },
  };
});
