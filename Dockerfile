FROM python:3.12-alpine AS build

WORKDIR /src
COPY build.py ./
COPY index.html 404.html styles.css script.js robots.txt sitemap.xml ./
COPY assets ./assets
COPY howto ./howto
COPY docs ./docs

RUN python3 build.py --root /src --out /out

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /out /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
