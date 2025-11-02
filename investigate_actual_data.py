#!/usr/bin/env python3
"""调查实际交易数据，分析盈亏比与胜率矛盾的原因"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import deepseekok2

def investigate_actual_data():
    """调查实际交易数据"""
    print("🔍 调查实际交易数据")
    print("=" * 50)
    
    # 1. 检查当前AI决策数据
    print("\n📊 1. 当前AI决策数据")
    print("-" * 30)
    
    ai_decisions = deepseekok2.web_data.get('ai_decisions', [])
    print(f"AI决策记录数量: {len(ai_decisions)}")
    
    if ai_decisions:
        print("\n最近的AI决策:")
        for i, decision in enumerate(ai_decisions[-3:], 1):  # 显示最近3条
            print(f"  {i}. 时间: {decision.get('timestamp', 'N/A')}")
            print(f"     信号: {decision.get('signal', 'N/A')}")
            print(f"     信心: {decision.get('confidence', 'N/A')}")
            print(f"     当前价格: {decision.get('current_price', 'N/A')}")
            print(f"     止损: {decision.get('stop_loss', 'N/A')}")
            print(f"     止盈: {decision.get('take_profit', 'N/A')}")
            
            # 计算盈亏比
            current_price = decision.get('current_price', 0)
            stop_loss = decision.get('stop_loss', 0)
            take_profit = decision.get('take_profit', 0)
            
            if current_price and stop_loss and take_profit and decision.get('signal') != 'HOLD':
                signal = decision.get('signal')
                if signal == 'BUY':
                    potential_profit = abs(take_profit - current_price)
                    potential_loss = abs(current_price - stop_loss)
                elif signal == 'SELL':
                    potential_profit = abs(current_price - take_profit)
                    potential_loss = abs(stop_loss - current_price)
                else:
                    potential_profit = potential_loss = 0
                
                if potential_loss > 0:
                    risk_reward = potential_profit / potential_loss
                    print(f"     计算盈亏比: {risk_reward:.2f}:1")
                else:
                    print(f"     计算盈亏比: 无法计算")
            else:
                print(f"     计算盈亏比: HOLD信号或数据不足")
            print()
    
    # 2. 检查交易历史数据
    print(f"📈 2. 交易历史数据")
    print("-" * 30)
    
    trade_history = deepseekok2.web_data.get('trade_history', [])
    print(f"交易历史记录数量: {len(trade_history)}")
    
    if trade_history:
        print("\n最近的交易记录:")
        for i, trade in enumerate(trade_history[-5:], 1):  # 显示最近5条
            print(f"  {i}. 时间: {trade.get('timestamp', 'N/A')}")
            print(f"     类型: {trade.get('type', 'N/A')}")
            print(f"     价格: {trade.get('price', 'N/A')}")
            print(f"     数量: {trade.get('amount', 'N/A')}")
            print(f"     盈亏: {trade.get('pnl', 'N/A')}")
            print()
    
    # 3. 检查性能统计
    print(f"📊 3. 性能统计")
    print("-" * 30)
    
    performance = deepseekok2.web_data.get('performance', {})
    print(f"总盈亏: {performance.get('total_profit', 'N/A')}")
    print(f"胜率: {performance.get('win_rate', 'N/A')}")
    print(f"总交易数: {performance.get('total_trades', 'N/A')}")
    
    # 4. 尝试从数据库获取更详细的数据
    print(f"\n💾 4. 数据库交易数据")
    print("-" * 30)
    
    try:
        # 尝试获取数据库中的交易数据
        from paper_trading import get_all_trades, compute_win_rate_from_db
        
        all_trades = get_all_trades()
        if all_trades:
            print(f"数据库中的交易记录: {len(all_trades)}")
            
            # 分析交易数据
            winning_trades = []
            losing_trades = []
            total_profit = 0
            
            print(f"\n详细交易分析:")
            for i, trade in enumerate(all_trades[-10:], 1):  # 分析最近10笔交易
                trade_id = trade.get('id', i)
                trade_type = trade.get('type', 'unknown')
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', 0)
                pnl = trade.get('pnl', 0)
                status = trade.get('status', 'unknown')
                
                print(f"  交易{trade_id}: {trade_type} | 入场:{entry_price} | 出场:{exit_price} | 盈亏:{pnl:+.2f} | 状态:{status}")
                
                if pnl > 0:
                    winning_trades.append(trade)
                elif pnl < 0:
                    losing_trades.append(trade)
                
                total_profit += pnl
            
            # 计算实际统计
            total_trades = len([t for t in all_trades if t.get('pnl', 0) != 0])
            winning_count = len([t for t in all_trades if t.get('pnl', 0) > 0])
            
            if total_trades > 0:
                actual_win_rate = winning_count / total_trades
                print(f"\n实际统计:")
                print(f"  总交易数: {total_trades}")
                print(f"  盈利交易: {winning_count}")
                print(f"  实际胜率: {actual_win_rate:.1%}")
                print(f"  总盈亏: {sum(t.get('pnl', 0) for t in all_trades):+.2f}")
                
                # 计算平均盈亏比
                if winning_trades and losing_trades:
                    avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
                    avg_loss = abs(sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades))
                    
                    if avg_loss > 0:
                        actual_risk_reward = avg_win / avg_loss
                        print(f"  平均盈利: {avg_win:.2f}")
                        print(f"  平均亏损: {avg_loss:.2f}")
                        print(f"  实际盈亏比: {actual_risk_reward:.2f}:1")
                        
                        # 计算理论盈亏平衡点
                        breakeven_rate = 1 / (1 + actual_risk_reward)
                        print(f"  理论盈亏平衡胜率: {breakeven_rate:.1%}")
                        
                        if actual_win_rate > breakeven_rate:
                            print(f"  ✅ 胜率高于平衡点，盈利合理")
                        else:
                            print(f"  ❌ 胜率低于平衡点，理论上应该亏损")
            
        else:
            print("数据库中没有交易记录")
            
    except Exception as e:
        print(f"无法访问数据库: {e}")
    
    # 5. 检查模拟数据
    print(f"\n🎮 5. 模拟交易数据")
    print("-" * 30)
    
    try:
        # 检查是否有模拟持仓数据
        current_position = deepseekok2.get_current_position()
        print(f"当前持仓: {current_position}")
        
        # 检查模拟持仓计算
        paper_position = deepseekok2.compute_paper_position()
        print(f"模拟持仓: {paper_position}")
        
    except Exception as e:
        print(f"无法获取持仓数据: {e}")
    
    # 6. 总结分析
    print(f"\n🎯 6. 分析总结")
    print("-" * 30)
    
    print("可能的原因:")
    print("1. 📊 数据来源问题:")
    print("   • AI决策数据与实际交易数据不匹配")
    print("   • 模拟交易与真实交易的差异")
    print("   • 数据库连接问题导致数据不完整")
    
    print(f"\n2. 🧮 计算方法问题:")
    print("   • 盈亏比计算使用计划价格而非实际价格")
    print("   • 胜率统计可能包含未完成的交易")
    print("   • 手续费和滑点未纳入计算")
    
    print(f"\n3. 🔄 系统状态问题:")
    print("   • 当前系统可能处于测试模式")
    print("   • AI功能不可用，使用备用数据")
    print("   • 数据库配置问题")
    
    print(f"\n建议:")
    print("✅ 检查系统配置和数据库连接")
    print("✅ 验证交易数据的完整性和准确性")
    print("✅ 重新计算基于实际成交数据的盈亏比")
    print("✅ 确认胜率统计的计算方法")

if __name__ == "__main__":
    investigate_actual_data()