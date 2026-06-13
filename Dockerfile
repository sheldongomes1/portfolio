# sheldongomes.dev — static site on Cloud Run (nginx).
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html favicon.ico favicon.svg favicon-16.png favicon-32.png \
     apple-touch-icon.png og-card.png Resume.pdf /usr/share/nginx/html/
EXPOSE 8080
