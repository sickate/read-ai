#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

def test_ai_correction_api():
    """测试AI批改作文API"""
    url = "http://localhost:5000/api/correct-essay"
    
    # 测试文本 - 包含一些错误的作文
    test_cases = [
        {
            "name": "包含错误的作文",
            "text": """我的家乡
            我的家乡是一个美丽的地方。那里有高山，有河流，有绿树。
            我每天都能看到鸟儿在天空中飞舞着。树上的叶子绿绿的，很好看。
            我喜欢在河边钓鱼，钓到鱼的时候心情特别高兴。
            家乡的人们都很友善，他们热情的招待客人。
            我希望我的家乡能够变的更加美丽。"""
        },
        {
            "name": "语法错误较多的作文", 
            "text": """我的梦想
            我有一个伟大的梦想，就是当一名医生。因为医生可以救死扶伤，帮助病人恢复健康。
            我觉得这是一个很有意义的职业。我要努力学习，争取考上好的医学院。
            虽然学医很辛苦，但是我相信只要努力就一定能够成功的。
            我要为了我的梦想而奋斗！"""
        }
    ]
    
    print("🤖 开始测试AI批改作文API...")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n📝 测试用例: {test_case['name']}")
        print(f"输入文本长度: {len(test_case['text'])} 字符")
        
        try:
            # 发送POST请求
            print("正在发送请求...")
            response = requests.post(
                url,
                json={"text": test_case['text']},
                headers={"Content-Type": "application/json"},
                timeout=60  # 增加超时时间，因为AI批改可能需要较长时间
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    corrections = result.get('corrections', [])
                    print(f"✅ 批改成功!")
                    print(f"   发现 {len(corrections)} 个修改类别")
                    
                    # 显示批改结果
                    total_issues = 0
                    for correction in corrections:
                        issue_count = len(correction.get('items', []))
                        total_issues += issue_count
                        print(f"   - {correction.get('type')}: {issue_count} 项")
                        
                        # 显示前3个修改建议作为示例
                        for i, item in enumerate(correction.get('items', [])[:3]):
                            print(f"     {i+1}. {item}")
                        if len(correction.get('items', [])) > 3:
                            print(f"     ... 还有 {len(correction.get('items', []))-3} 项")
                    
                    print(f"   总计发现问题: {total_issues} 处")
                    
                    # 显示原始响应（可选）
                    if result.get('raw_response'):
                        print(f"\n📄 AI原始响应预览:")
                        raw_preview = result['raw_response'][:200] + "..." if len(result['raw_response']) > 200 else result['raw_response']
                        print(f"   {raw_preview}")
                        
                else:
                    print(f"❌ API返回错误: {result.get('error')}")
            else:
                print(f"❌ HTTP错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保Flask应用正在运行 (python -m app)")
            break
        except requests.exceptions.Timeout:
            print("❌ 请求超时: AI处理时间过长，请稍后重试")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 测试完成!")

if __name__ == "__main__":
    test_ai_correction_api() 