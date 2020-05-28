#!/bin/bash
echo "Остановка демона Odoo"
sudo service odoo-server stop
echo "Ожидание 10 секунд ..."
sleep 10s
echo "Запуск демона Odoo"
sudo service odoo-server start
