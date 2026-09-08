FROM python:3.12-alpine AS build

WORKDIR /src
COPY requirements-build.txt ./
RUN pip install --no-cache-dir -r requirements-build.txt
COPY build.py compress_assets.py ./
COPY index.html 404.html styles.css script.js robots.txt sitemap.xml ./
COPY assets ./assets
COPY design ./design
COPY src ./src
COPY howto ./howto
COPY docs ./docs

# Copy site, compress oversized assets (200KB / 50KB), stamp cache-busting URLs.
RUN python3 build.py --root /src --out /out

FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /out /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
