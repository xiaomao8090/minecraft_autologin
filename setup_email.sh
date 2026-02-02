#!/bin/bash

echo "邮件告警配置向导"
echo "================"
echo ""
echo "使用Gmail发送告警邮件需要："
echo "1. 一个Gmail账号"
echo "2. 开启两步验证"
echo "3. 生成应用专用密码"
echo ""
echo "生成应用专用密码步骤："
echo "1. 访问 https://myaccount.google.com/security"
echo "2. 开启两步验证"
echo "3. 搜索'应用专用密码'"
echo "4. 选择'邮件'和'其他设备'"
echo "5. 生成密码（16位，无空格）"
echo ""
echo "================"
echo ""

read -p "发件人Gmail地址: " SENDER_EMAIL
read -sp "应用专用密码（16位）: " APP_PASSWORD
echo ""
read -p "收件人邮箱（多个用逗号分隔，留空则发送给自己）: " RECEIVER_EMAIL

if [ -z "$RECEIVER_EMAIL" ]; then
    RECEIVER_EMAIL=$SENDER_EMAIL
fi

ENV_FILE=".env"

# 确保.env文件存在
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

# 移除可能存在的旧配置
sed -i.bak '/^ALERT_EMAIL=/d' "$ENV_FILE" 2>/dev/null
sed -i.bak '/^ALERT_EMAIL_PASSWORD=/d' "$ENV_FILE" 2>/dev/null
sed -i.bak '/^ALERT_RECEIVER_EMAIL=/d' "$ENV_FILE" 2>/dev/null
rm -f "$ENV_FILE.bak"

# 添加新配置
echo "" >> "$ENV_FILE"
echo "ALERT_EMAIL=$SENDER_EMAIL" >> "$ENV_FILE"
echo "ALERT_EMAIL_PASSWORD=$APP_PASSWORD" >> "$ENV_FILE"
echo "ALERT_RECEIVER_EMAIL=$RECEIVER_EMAIL" >> "$ENV_FILE"

echo ""
echo "配置已保存到 .env 文件"
echo "收件人: $RECEIVER_EMAIL"
echo ""
echo "测试邮件发送..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export ALERT_EMAIL="$SENDER_EMAIL"
export ALERT_EMAIL_PASSWORD="$APP_PASSWORD"
export ALERT_RECEIVER_EMAIL="$RECEIVER_EMAIL"

"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/email_alert.py" "测试邮件" "这是一封测试邮件，如果收到说明配置成功！" "info"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 邮件配置成功！"
    echo "✓ 请检查收件箱（可能在垃圾邮件中）"
else
    echo ""
    echo "✗ 邮件发送失败，请检查配置"
    echo "常见问题："
    echo "1. 应用专用密码是否正确（16位，无空格）"
    echo "2. 是否开启了两步验证"
    echo "3. 网络是否能访问Gmail"
fi
