#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

def test_word_counter_api():
    """测试字数统计API"""
    url = "http://localhost:5000/api/analyze-text"
    
    # 测试文本
    test_cases = [
        {
            "name": "中英文混合",
            "text": "你好，世界！Hello, world! 这是一个测试。This is a test."
        },
        {
            "name": "纯中文",
            "text": "今天天气真好，我们去公园散步吧。"
        },
        {
            "name": "纯英文",
            "text": "The quick brown fox jumps over the lazy dog."
        },
        {
            "name": "空文本",
            "text": ""
        }
    ]
    
    print("🧪 开始测试字数统计API...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📝 测试用例: {test_case['name']}")
        print(f"输入文本: '{test_case['text']}'")
        
        try:
            # 发送POST请求
            response = requests.post(
                url,
                json={"text": test_case['text']},
                headers={"Content-Type": "application/json"}
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    analysis = result['result']
                    print(f"✅ 成功!")
                    print(f"   汉字: {analysis['chinese_chars']}")
                    print(f"   英文单词: {analysis['english_words']}")
                    print(f"   标点符号: {analysis['punctuation']}")
                    print(f"   总字符: {analysis['total_chars']}")
                else:
                    print(f"❌ API返回错误: {result.get('error')}")
            else:
                print(f"❌ HTTP错误: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败: 请确保Flask应用正在运行 (python -m app)")
            break
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成!")

if __name__ == "__main__":
    test_word_counter_api() 