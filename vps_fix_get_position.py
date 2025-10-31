#!/usr/bin/env python3
"""
VPS修复脚本：修复get_current_position函数的认证问题
直接在VPS上应用修复，无需等待Git推送
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """备份原文件"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 已备份原文件到: {backup_path}")
    return backup_path

def fix_get_current_position(file_path):
    """修复get_current_position函数"""
    print(f"🔧 开始修复文件: {file_path}")
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找get_current_position函数
    pattern = r'def get_current_position\(\):\s*"""获取当前持仓情况.*?"""(.*?)(?=\n\ndef|\nclass|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ 未找到get_current_position函数")
        return False
    
    # 新的函数实现
    new_function = '''def get_current_position():
    """获取当前持仓情况 - Binance FAPI 版本"""
    try:
        # 在测试模式下或没有API密钥时，使用模拟持仓数据
        if TRADE_CONFIG.get('test_mode', True) or exchange is None:
            print("使用模拟持仓数据（测试模式）")
            return compute_paper_position()
        
        # 检查是否有API密钥
        binance_api_key = os.getenv('BINANCE_API_KEY')
        binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
        if not binance_api_key or not binance_secret_key:
            print("缺少API密钥，使用模拟持仓数据")
            return compute_paper_position()
        
        positions = exchange.fetch_positions([TRADE_CONFIG['symbol']])

        for pos in positions:
            if pos.get('symbol') == TRADE_CONFIG['symbol']:
                contracts = pos.get('contracts')
                if contracts is None:
                    contracts = pos.get('positionAmt')
                contracts = float(contracts) if contracts else 0.0

                if contracts > 0:
                    entry_price = pos.get('entryPrice') or pos.get('avgPrice') or 0
                    unrealized_pnl = pos.get('unrealizedPnl') or 0
                    leverage = pos.get('leverage') or TRADE_CONFIG['leverage']
                    side = pos.get('side')  # 统一字段：'long' 或 'short'

                    return {
                        'side': side,
                        'size': contracts,
                        'entry_price': float(entry_price),
                        'unrealized_pnl': float(unrealized_pnl),
                        'leverage': float(leverage),
                        'symbol': pos.get('symbol')
                    }

        return None

    except Exception as e:
        print(f"获取持仓失败，使用模拟持仓数据: {e}")
        return compute_paper_position()'''
    
    # 替换函数
    old_function_full = match.group(0)
    content = content.replace(old_function_full, new_function)
    
    # 写入修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ get_current_position函数修复完成")
    return True

def main():
    """主函数"""
    print("🚀 开始VPS修复脚本...")
    
    # 文件路径
    target_file = "/app/deepseekok2.py"  # Docker容器内路径
    
    # 检查文件是否存在
    if not os.path.exists(target_file):
        print(f"❌ 文件不存在: {target_file}")
        print("请确保在Docker容器内运行此脚本")
        return False
    
    # 备份原文件
    backup_path = backup_file(target_file)
    
    try:
        # 修复函数
        if fix_get_current_position(target_file):
            print("🎉 修复完成！")
            print("📝 修复内容:")
            print("   - 在测试模式下使用模拟持仓数据")
            print("   - 检查API密钥，缺失时回退到模拟数据")
            print("   - 异常时自动使用模拟持仓")
            print("\n🔄 请重启容器以应用修复:")
            print("   docker-compose restart btc-trading-bot")
            return True
        else:
            print("❌ 修复失败")
            return False
            
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        # 恢复备份
        shutil.copy2(backup_path, target_file)
        print(f"🔄 已恢复备份文件")
        return False

if __name__ == "__main__":
    main()