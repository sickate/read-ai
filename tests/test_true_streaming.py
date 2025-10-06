import requests
import json
import time

API_KEY = "AIzaSyCLTti_Oiev2vO1UehuvoxnabZv7xXhnO0"
BASE_URL = "https://gemini.parallelstreamllc.com/v1beta"
MODEL = "gemini-2.5-flash-lite-preview-06-17"

def test_real_streaming():
    headers = {
        'x-goog-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 测试更长的内容，看是否能触发真正的流式
    payload = {
        "contents": [{"parts": [{"text": "Write a story about a robot learning to paint. Make it at least 500 words long. Output the story word by word."}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    
    url = f"{BASE_URL}/models/{MODEL}:generateContent?alt=sse"
    
    print("Testing real-time streaming...")
    print("-" * 50)
    
    start_time = time.time()
    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    chunk_count = 0
    total_text = ""
    
    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
        if chunk:
            chunk_count += 1
            total_text += chunk
            
            # 每收到100个字符打印一次
            if chunk_count % 100 == 0:
                elapsed = time.time() - start_time
                print(f"Received {chunk_count} chars in {elapsed:.2f}s")
    
    print(f"\nTotal chunks: {chunk_count}")
    print(f"Total time: {time.time() - start_time:.2f}s")
    print(f"Response starts with: {total_text[:200]}...")
    
    # 检查是否是完整的SSE响应
    if total_text.startswith('data: '):
        lines = total_text.split('\n')
        print(f"Number of SSE events: {len([l for l in lines if l.startswith('data: ')])}")

test_real_streaming()
