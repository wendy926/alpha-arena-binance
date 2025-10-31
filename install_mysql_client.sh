#!/bin/bash
# 安装MySQL客户端脚本

echo "🔧 安装MySQL客户端"
echo "=================="

# 检测操作系统
if [ -f /etc/redhat-release ]; then
    OS="centos"
elif [ -f /etc/debian_version ]; then
    OS="ubuntu"
else
    echo "❌ 无法识别操作系统"
    exit 1
fi

echo "📋 检测到操作系统: $OS"

# 根据操作系统安装MySQL客户端
if [ "$OS" = "centos" ]; then
    echo "🔧 在CentOS上安装MySQL客户端..."
    
    # 方法1: 安装MySQL客户端
    echo "方法1: 安装mysql客户端包"
    yum install -y mysql
    
    if [ $? -ne 0 ]; then
        echo "方法2: 安装mariadb客户端"
        yum install -y mariadb
    fi
    
    if [ $? -ne 0 ]; then
        echo "方法3: 安装MySQL社区版客户端"
        yum install -y mysql-community-client
    fi
    
elif [ "$OS" = "ubuntu" ]; then
    echo "🔧 在Ubuntu上安装MySQL客户端..."
    
    # 更新包列表
    apt-get update
    
    # 安装MySQL客户端
    apt-get install -y mysql-client
    
    if [ $? -ne 0 ]; then
        echo "尝试安装mariadb客户端"
        apt-get install -y mariadb-client
    fi
fi

# 验证安装
echo ""
echo "🔍 验证安装结果:"
if command -v mysql >/dev/null 2>&1; then
    echo "✅ MySQL客户端安装成功"
    mysql --version
    
    echo ""
    echo "💡 现在你可以使用以下命令连接数据库:"
    echo "mysql -u root -p"
    echo ""
    echo "或者指定主机:"
    echo "mysql -h localhost -u root -p"
    
else
    echo "❌ MySQL客户端安装失败"
    echo ""
    echo "🔧 替代方案:"
    echo "1. 使用Python脚本检查数据库:"
    echo "   python3 vps_db_direct_check.py"
    echo ""
    echo "2. 手动下载MySQL客户端:"
    echo "   wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm"
    echo "   rpm -ivh mysql80-community-release-el7-3.noarch.rpm"
    echo "   yum install mysql-community-client"
fi

echo ""
echo "=================="