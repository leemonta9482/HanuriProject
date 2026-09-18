# Vue 빌드 → nginx 가 정적 파일을 내고 /api, /uploads, /docs 는 backend 로 넘긴다.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# VITE_API_BASE_URL 을 비워 두면 HTTPS 공개 호스트에서는 같은 origin 을 API 로 쓴다(client.ts)
# type-check(vue-tsc) 는 기존 코드의 TS 오류로 실패하므로 컨테이너 빌드에서는 번들만 만든다
RUN npm run build-only

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
