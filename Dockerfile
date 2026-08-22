FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html 404.html styles.css script.js /usr/share/nginx/html/
COPY assets /usr/share/nginx/html/assets
COPY howto /usr/share/nginx/html/howto
COPY docs /usr/share/nginx/html/docs

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
