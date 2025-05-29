FROM php:latest
RUN docker-php-ext-install pdo_mysql
COPY . /app
WORKDIR /app
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN composer install
EXPOSE 80
CMD ["php", "yii serve --port=8000"]