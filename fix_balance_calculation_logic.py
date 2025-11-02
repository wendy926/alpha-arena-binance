#!/usr/bin/env python3
"""修复可用余额计算逻辑
当前：起始金额 + 未实现盈亏
期望：起始金额 + 总盈亏
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def analyze_current_logic():
    """分析当前的余额计算逻辑"""
    print("🔍 分析当前可用余额计算逻辑")
    print("=" * 60)
    
    print("\n📊 当前逻辑分析:")
    print("1. deepseekok2.py 中的计算:")
    print("   adjusted_balance = balance['USDT']['free'] + unrealized_pnl")
    print("   • balance['USDT']['free']: 交易所账户余额")
    print("   • unrealized_pnl: 当前持仓的未实现盈亏")
    
    print("\n2. web_server.py 中的计算:")
    print("   adjusted_balance = balance['USDT']['free'] + unrealized_pnl")
    print("   • 同样使用未实现盈亏")
    
    print("\n❌ 问题分析:")
    print("   • 当前逻辑只考虑未实现盈亏，忽略了历史已实现盈亏")
    print("   • 如果有历史交易盈利，但当前无持仓，可用余额不会反映历史盈利")
    print("   • 可用余额应该反映总的盈亏情况，而不仅仅是当前持仓")
    
    print("\n✅ 期望逻辑:")
    print("   adjusted_balance = initial_balance + total_profit")
    print("   • initial_balance: 起始金额")
    print("   • total_profit: 总盈亏（历史已实现 + 当前未实现）")
    
    print("\n🎯 修复方案:")
    print("   1. 获取历史已实现盈亏（从数据库）")
    print("   2. 获取当前未实现盈亏（从持仓）")
    print("   3. 计算总盈亏 = 历史已实现 + 当前未实现")
    print("   4. 可用余额 = 起始金额 + 总盈亏")

def create_balance_calculation_function():
    """创建新的余额计算函数"""
    print("\n🔧 创建新的余额计算函数")
    print("=" * 60)
    
    function_code = '''
def calculate_adjusted_balance(initial_balance=10000.0):
    """
    计算调整后的可用余额
    逻辑：起始金额 + 总盈亏（历史已实现 + 当前未实现）
    """
    try:
        # 1. 获取历史已实现盈亏（从数据库）
        from paper_trading import compute_win_rate_from_db
        stats = compute_win_rate_from_db()
        historical_profit = stats.get('total_profit', 0.0)
        
        # 2. 获取当前未实现盈亏（从持仓）
        current_position = get_current_position()
        unrealized_pnl = current_position.get('unrealized_pnl', 0) if current_position else 0
        
        # 3. 计算总盈亏
        total_profit = historical_profit + unrealized_pnl
        
        # 4. 计算调整后的余额
        adjusted_balance = initial_balance + total_profit
        
        return {
            'initial_balance': initial_balance,
            'historical_profit': historical_profit,
            'unrealized_pnl': unrealized_pnl,
            'total_profit': total_profit,
            'adjusted_balance': adjusted_balance
        }
        
    except Exception as e:
        print(f"计算调整后余额失败: {e}")
        return {
            'initial_balance': initial_balance,
            'historical_profit': 0.0,
            'unrealized_pnl': 0.0,
            'total_profit': 0.0,
            'adjusted_balance': initial_balance
        }
'''
    
    print("新的余额计算函数:")
    print(function_code)
    
    return function_code

def show_comparison():
    """显示修复前后的对比"""
    print("\n📊 修复前后对比")
    print("=" * 60)
    
    print("🔴 修复前（当前逻辑）:")
    print("   场景1：有历史盈利$500，当前无持仓")
    print("   • 历史已实现盈亏: +$500")
    print("   • 当前未实现盈亏: $0")
    print("   • 当前计算: $10,000 + $0 = $10,000")
    print("   • ❌ 问题：忽略了历史盈利$500")
    
    print("\n   场景2：有历史亏损$200，当前盈利$300")
    print("   • 历史已实现盈亏: -$200")
    print("   • 当前未实现盈亏: +$300")
    print("   • 当前计算: $10,000 + $300 = $10,300")
    print("   • ❌ 问题：忽略了历史亏损$200")
    
    print("\n🟢 修复后（期望逻辑）:")
    print("   场景1：有历史盈利$500，当前无持仓")
    print("   • 历史已实现盈亏: +$500")
    print("   • 当前未实现盈亏: $0")
    print("   • 新计算: $10,000 + ($500 + $0) = $10,500")
    print("   • ✅ 正确：反映了历史盈利")
    
    print("\n   场景2：有历史亏损$200，当前盈利$300")
    print("   • 历史已实现盈亏: -$200")
    print("   • 当前未实现盈亏: +$300")
    print("   • 新计算: $10,000 + (-$200 + $300) = $10,100")
    print("   • ✅ 正确：反映了净盈利$100")

def main():
    """主函数"""
    print("🔧 可用余额计算逻辑修复分析")
    print("=" * 60)
    
    analyze_current_logic()
    create_balance_calculation_function()
    show_comparison()
    
    print("\n🎯 下一步操作:")
    print("1. 修改 deepseekok2.py 中的余额计算逻辑")
    print("2. 修改 web_server.py 中的余额计算逻辑")
    print("3. 测试修复后的计算是否正确")
    print("4. 确保前端正确显示调整后的余额")

if __name__ == "__main__":
    main()