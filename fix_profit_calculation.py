#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复盈亏计算问题
解决price/amount为None或0导致盈亏为0的问题
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_compute_win_rate_function():
    """修复compute_win_rate_from_db函数中的盈亏计算逻辑"""
    
    # 读取原文件
    file_path = os.path.join(os.path.dirname(__file__), 'paper_trading.py')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找需要修复的代码段
    old_code = '''    for t in trades:
        action = (t.get('action') or '').lower()
        price = float(t.get('price') or 0.0)
        amount = float(t.get('amount') or 0.0)'''
    
    # 修复后的代码
    new_code = '''    for t in trades:
        action = (t.get('action') or '').lower()
        
        # 修复：如果price或amount为None/空，跳过这条记录
        raw_price = t.get('price')
        raw_amount = t.get('amount')
        
        if raw_price is None or raw_price == '' or raw_amount is None or raw_amount == '':
            print(f"⚠️ 跳过无效记录: action={action}, price={raw_price}, amount={raw_amount}")
            continue
            
        try:
            price = float(raw_price)
            amount = float(raw_amount)
            
            # 检查是否为0值
            if price <= 0 or amount <= 0:
                print(f"⚠️ 跳过零值记录: action={action}, price={price}, amount={amount}")
                continue
                
        except (ValueError, TypeError):
            print(f"⚠️ 跳过无法转换的记录: action={action}, price={raw_price}, amount={raw_amount}")
            continue'''
    
    if old_code in content:
        # 替换代码
        new_content = content.replace(old_code, new_code)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 成功修复 compute_win_rate_from_db 函数")
        return True
    else:
        print("❌ 未找到需要修复的代码段")
        return False

def create_backup():
    """创建备份文件"""
    import shutil
    
    source = os.path.join(os.path.dirname(__file__), 'paper_trading.py')
    backup = os.path.join(os.path.dirname(__file__), 'paper_trading.py.backup')
    
    try:
        shutil.copy2(source, backup)
        print(f"✅ 已创建备份文件: {backup}")
        return True
    except Exception as e:
        print(f"❌ 创建备份失败: {e}")
        return False

def test_fixed_function():
    """测试修复后的函数"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 重新导入模块以获取修复后的函数
        import importlib
        import paper_trading
        importlib.reload(paper_trading)
        
        print("\n🧪 测试修复后的胜率计算:")
        stats = paper_trading.compute_win_rate_from_db()
        
        print(f"📊 修复后结果:")
        print(f"   胜率: {stats.get('win_rate', 0)}%")
        print(f"   总交易次数: {stats.get('total_trades', 0)}")
        print(f"   总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        return stats
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_web_data():
    """更新web_data中的performance数据"""
    try:
        import deepseekok2
        
        # 重新计算胜率
        from paper_trading import compute_win_rate_from_db
        stats = compute_win_rate_from_db()
        
        # 更新web_data
        if 'performance' not in deepseekok2.web_data:
            deepseekok2.web_data['performance'] = {}
        
        deepseekok2.web_data['performance'].update({
            'win_rate': stats.get('win_rate', 0),
            'total_trades': stats.get('total_trades', 0),
            'total_profit': stats.get('total_profit', 0)
        })
        
        print("✅ 已更新web_data中的performance数据")
        return True
        
    except Exception as e:
        print(f"❌ 更新web_data失败: {e}")
        return False

def main():
    print("🔧 修复盈亏计算问题")
    print("="*50)
    
    # 1. 创建备份
    print("\n1. 创建备份文件...")
    if not create_backup():
        print("❌ 备份失败，停止修复")
        return
    
    # 2. 修复函数
    print("\n2. 修复compute_win_rate_from_db函数...")
    if not fix_compute_win_rate_function():
        print("❌ 修复失败")
        return
    
    # 3. 测试修复结果
    print("\n3. 测试修复后的函数...")
    stats = test_fixed_function()
    
    if stats:
        # 4. 更新web_data
        print("\n4. 更新web_data...")
        update_web_data()
        
        print("\n" + "="*50)
        print("🎉 修复完成！")
        print("="*50)
        print(f"修复后胜率: {stats.get('win_rate', 0)}%")
        print(f"修复后总交易: {stats.get('total_trades', 0)}")
        print(f"修复后总盈亏: ${stats.get('total_profit', 0):.2f}")
        print("\n💡 建议:")
        print("1. 重启web服务器以应用修复")
        print("2. 检查网站显示是否正常")
        print("3. 如果问题仍然存在，检查数据库中的原始数据")
    else:
        print("❌ 测试失败，请检查修复代码")

if __name__ == "__main__":
    main()