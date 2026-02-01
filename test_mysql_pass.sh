#!/bin/bash
echo "测试MySQL密码"
echo "============="
echo ""
read -sp "请输入MySQL密码: " PASS
echo ""
mysql -u root -p"$PASS" -e "SELECT 'Success!' as Result;"
