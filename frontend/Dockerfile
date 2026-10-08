# 第一阶段：Node 打包 Vue 源码为静态文件
FROM docker.m.daocloud.io/library/node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --registry=https://mirrors.cloud.tencent.com/npm/
COPY . .
RUN npm run build

# 第二阶段：Nginx 托管静态文件
FROM docker.m.daocloud.io/library/nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
