#!/usr/bin/env python3
"""检查实际交易数据，找出25%胜率和0.69:1盈亏比的来源"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from paper_trading import get_all_trades, compute_win_rate_from_db
    import deepseekok2
    print("✅ 成功导入模块")
except Exception as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

def analyze_actual_data():
    """分析实际的交易数据"""
    print("🔍 检查实际交易数据")
    print("=" * 50)
    
    # 1. 检查数据库中的交易记录
    print("\n1️⃣ 数据库交易记录:")
    try:
        trades = get_all_trades()
        if trades:
            print(f"   总记录数: {len(trades)}")
            print("   最近5条记录:")
            for i, trade in enumerate(trades[-5:]):
                print(f"     {i+1}. {trade}")
        else:
            print("   ❌ 数据库中没有交易记录")
    except Exception as e:
        print(f"   ❌ 读取数据库失败: {e}")
    
    # 2. 计算胜率统计
    print("\n2️⃣ 胜率统计:")
    try:
        stats = compute_win_rate_from_db()
        print(f"   胜率: {stats.get('win_rate', 0):.1f}%")
        print(f"   总交易: {stats.get('total_trades', 0)}")
        print(f"   总盈亏: ${stats.get('total_profit', 0):.2f}")
        
        # 检查是否是25%胜率
        if abs(stats.get('win_rate', 0) - 25.0) < 0.1:
            print("   ✅ 找到25%胜率的来源！")
        else:
            print(f"   ⚠️ 当前胜率不是25%")
    except Exception as e:
        print(f"   ❌ 计算胜率失败: {e}")
    
    # 3. 检查内存中的AI决策数据
    print("\n3️⃣ AI决策数据:")
    try:
        decisions = deepseekok2.ai_decisions
        if decisions:
            print(f"   AI决策记录数: {len(decisions)}")
            
            # 分析最近的决策
            risk_rewards = []
            for decision in decisions[-10:]:  # 最近10条
                if decision.get('signal') in ['BUY', 'SELL']:
                    current_price = decision.get('price', 0)
                    stop_loss = decision.get('stop_loss', 0)
                    take_profit = decision.get('take_profit', 0)
                    
                    if current_price > 0 and stop_loss > 0 and take_profit > 0:
                        if decision['signal'] == 'BUY':
                            potential_profit = take_profit - current_price
                            potential_loss = current_price - stop_loss
                        else:  # SELL
                            potential_profit = current_price - take_profit
                            potential_loss = stop_loss - current_price
                        
                        if potential_loss > 0:
                            risk_reward = potential_profit / potential_loss
                            risk_rewards.append(risk_reward)
                            print(f"     决策: {decision['signal']}, 盈亏比: {risk_reward:.2f}:1")
            
            if risk_rewards:
                avg_rr = sum(risk_rewards) / len(risk_rewards)
                print(f"   平均盈亏比: {avg_rr:.2f}:1")
                
                # 检查是否接近0.69:1
                if abs(avg_rr - 0.69) < 0.1:
                    print("   ✅ 找到0.69:1盈亏比的来源！")
                else:
                    print(f"   ⚠️ 当前平均盈亏比不是0.69:1")
            else:
                print("   ⚠️ 没有有效的盈亏比数据")
        else:
            print("   ❌ 内存中没有AI决策记录")
    except Exception as e:
        print(f"   ❌ 分析AI决策失败: {e}")
    
    # 4. 检查web_data中的性能数据
    print("\n4️⃣ Web性能数据:")
    try:
        performance = deepseekok2.web_data.get('performance', {})
        print(f"   显示胜率: {performance.get('win_rate', 0):.1f}%")
        print(f"   总交易: {performance.get('total_trades', 0)}")
        print(f"   总盈亏: ${performance.get('total_pnl', 0):.2f}")
    except Exception as e:
        print(f"   ❌ 读取性能数据失败: {e}")
    
    # 5. 检查交易历史
    print("\n5️⃣ 内存交易历史:")
    try:
        history = deepseekok2.trade_history
        if history:
            print(f"   交易历史记录数: {len(history)}")
            
            # 分析盈亏
            wins = 0
            total = 0
            total_pnl = 0
            
            for trade in history:
                pnl = trade.get('pnl', 0)
                if pnl != 0:  # 只统计已完成的交易
                    total += 1
                    total_pnl += pnl
                    if pnl > 0:
                        wins += 1
            
            if total > 0:
                win_rate = wins / total * 100
                print(f"   内存胜率: {win_rate:.1f}% ({wins}/{total})")
                print(f"   内存总盈亏: ${total_pnl:.2f}")
                
                # 检查是否是25%胜率
                if abs(win_rate - 25.0) < 0.1:
                    print("   ✅ 在内存交易历史中找到25%胜率！")
            else:
                print("   ⚠️ 没有已完成的交易")
        else:
            print("   ❌ 内存中没有交易历史")
    except Exception as e:
        print(f"   ❌ 分析交易历史失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 数据来源分析结论:")
    print("1. 如果在数据库中找到25%胜率 → 来源于实际交易记录")
    print("2. 如果在AI决策中找到0.69:1盈亏比 → 来源于AI决策设置")
    print("3. 如果在内存历史中找到25%胜率 → 来源于模拟交易")
    print("4. 需要验证这些数据的计算方法是否正确")

if __name__ == "__main__":
    analyze_actual_data()