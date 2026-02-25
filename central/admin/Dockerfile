FROM node:22-alpine AS base
WORKDIR /admin
COPY package.json ./
RUN npm install

FROM base AS dev
COPY . .
CMD ["npm", "run", "dev"]

FROM base AS build
COPY . .
ARG VITE_API_URL
ARG VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
RUN npm run build

FROM alpine AS prod
COPY --from=build /admin/dist /admin/dist
CMD ["/bin/sh", "-c", "cp -a /admin/dist/. /dist/"]