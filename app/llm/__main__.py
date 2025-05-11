"""
LLM 模块的命令行入口点
用于验证 LLM 功能
"""

import asyncio
import argparse
from . import generate_text

def main():
    parser = argparse.ArgumentParser(description="LLM 模块验证工具")
    parser.add_argument("--provider", "-p", default="aliyun", help="LLM 提供者 (aliyun, openai, siliconflow, xai, gemini)")
    parser.add_argument("--model", "-m", help="模型名称，如果不指定则使用默认模型")
    parser.add_argument("--prompt", default="你好，请介绍一下自己", help="提示文本")
    
    args = parser.parse_args()
    
    async def run():
        try:
            print(f"使用提供者: {args.provider}")
            print(f"模型: {args.model or '默认模型'}")
            print(f"提示: {args.prompt}")
            print("\n正在生成回复...\n")
            
            response = await generate_text(args.prompt, args.provider, args.model)
            print("回复:")
            print("-" * 50)
            print(response)
            print("-" * 50)
        except Exception as e:
            print(f"错误: {e}")
    
    asyncio.run(run())

if __name__ == "__main__":
    main()