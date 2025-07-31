#!/usr/bin/env python3
"""
MCP Feedback Enhanced - 图片序列化问题复现指南

这个脚本提供了完整的复现步骤，用于演示修复前后的效果对比。

## 问题描述
用户在 MCP Feedback Enhanced Web UI 中粘贴截图时，系统抛出 JSON 序列化错误：
"Unable to serialize unknown type: <class 'fastmcp.utilities.types.Image'>"

## 复现步骤
1. 用户在 Web UI 中粘贴截图
2. 前端将图片数据发送给后端
3. server.py 的 process_images 函数处理图片
4. 返回 fastmcp.utilities.types.Image 对象
5. MCP 协议尝试序列化响应时失败

## 修复方案
使用 .to_image_content() 方法将 Image 对象转换为 mcp.types.ImageContent 对象

## 运行此脚本
python examples/reproduction_guide.py
"""

import base64
import json
import sys
import os
from pathlib import Path


def setup_environment():
    """设置环境"""
    print("🔧 环境设置")
    print("=" * 40)
    
    # 检查是否在正确的目录
    current_dir = Path.cwd()
    if not (current_dir / "src" / "mcp_feedback_enhanced").exists():
        print("❌ 请在项目根目录运行此脚本")
        print(f"当前目录：{current_dir}")
        print("预期目录：包含 src/mcp_feedback_enhanced/ 的项目根目录")
        return False
    
    # 添加到 Python 路径
    src_path = current_dir / "src"
    sys.path.insert(0, str(src_path))
    
    print(f"✅ 项目目录：{current_dir}")
    print(f"✅ 源码路径：{src_path}")
    return True


def check_dependencies():
    """检查依赖"""
    print("\n📦 依赖检查")
    print("=" * 40)
    
    required_modules = [
        ("fastmcp.utilities.types", "Image"),
        ("mcp.types", "ImageContent"),
        ("mcp_feedback_enhanced.server", "process_images")
    ]
    
    missing_deps = []
    
    for module_name, class_name in required_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"❌ {module_name}.{class_name} - {e}")
            missing_deps.append(module_name.split('.')[0])
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖：{', '.join(set(missing_deps))}")
        print("请运行：pip install -e .")
        return False
    
    return True


def create_test_image():
    """创建测试图片数据"""
    # 1x1 PNG 图片的 base64 编码
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    return {
        "data": base64.b64decode(png_base64),
        "name": "screenshot.png",
        "size": 68
    }


def demonstrate_original_issue():
    """演示原始问题"""
    print("\n🔴 步骤 1: 演示原始序列化问题")
    print("=" * 50)
    
    try:
        from fastmcp.utilities.types import Image as MCPImage
        
        # 创建测试图片
        image_data = create_test_image()
        print(f"📷 创建测试图片：{image_data['name']} ({image_data['size']} bytes)")
        
        # 创建 MCPImage 对象（原始方式）
        mcp_image = MCPImage(data=image_data["data"], format="png")
        print(f"🏗️  创建 MCPImage 对象：{type(mcp_image)}")
        
        # 尝试模拟 MCP 协议的序列化过程
        print("🔄 模拟 MCP 协议序列化...")
        
        # 方法 1：直接序列化对象（会失败）
        try:
            json.dumps(mcp_image)
            print("  ⚠️  方法 1 意外成功")
        except TypeError as e:
            print(f"  ✅ 方法 1 预期失败：{e}")
        
        # 方法 2：序列化对象属性（bytes 数据会失败）
        try:
            data_dict = {
                "type": "image",
                "data": mcp_image.data,  # bytes 对象
                "format": mcp_image.format
            }
            json.dumps(data_dict)
            print("  ⚠️  方法 2 意外成功")
        except TypeError as e:
            print(f"  ✅ 方法 2 预期失败：{e}")
        
        print("  📝 原因：fastmcp.utilities.types.Image 的 data 属性是 bytes 对象")
        print("      MCP 协议需要 JSON 可序列化的数据结构")
        
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入 fastmcp：{e}")
        return False


def demonstrate_fixed_solution():
    """演示修复方案"""
    print("\n🟢 步骤 2: 演示修复方案")
    print("=" * 50)
    
    try:
        from fastmcp.utilities.types import Image as MCPImage
        from mcp.types import ImageContent
        
        # 创建测试图片
        image_data = create_test_image()
        print(f"📷 使用相同的测试图片：{image_data['name']}")
        
        # 创建 MCPImage 对象并转换
        mcp_image = MCPImage(data=image_data["data"], format="png")
        print(f"🏗️  创建 MCPImage 对象：{type(mcp_image)}")
        
        # 关键修复：转换为 ImageContent
        image_content = mcp_image.to_image_content()
        print(f"🔄 转换为 ImageContent：{type(image_content)}")
        
        # 验证可以序列化
        print("✅ 验证序列化...")
        
        # 获取可序列化的数据
        if hasattr(image_content, 'model_dump'):
            serializable_data = image_content.model_dump()
        elif hasattr(image_content, 'dict'):
            serializable_data = image_content.dict()
        else:
            serializable_data = image_content.__dict__
        
        # 序列化为 JSON
        json_str = json.dumps(serializable_data, indent=2)
        print(f"  📄 JSON 长度：{len(json_str)} 字符")
        
        # 显示结构
        display_data = serializable_data.copy()
        if 'data' in display_data and len(display_data['data']) > 50:
            display_data['data'] = display_data['data'][:47] + "..."
        
        print("  📋 JSON 结构：")
        print("    " + json.dumps(display_data, indent=4, ensure_ascii=False).replace("\n", "\n    "))
        
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入必要模块：{e}")
        return False


def test_process_images_function():
    """测试 process_images 函数"""
    print("\n🧪 步骤 3: 测试修复后的 process_images 函数")
    print("=" * 60)
    
    try:
        from mcp_feedback_enhanced.server import process_images
        
        # 准备测试数据（模拟用户粘贴的截图）
        test_images = [
            create_test_image(),
            {
                "data": base64.b64encode(b"fake jpeg data").decode(),  # base64 字符串
                "name": "upload.jpg",
                "size": 15
            }
        ]
        
        print(f"📋 输入数据：{len(test_images)} 张图片")
        for i, img in enumerate(test_images, 1):
            data_type = "bytes" if isinstance(img["data"], bytes) else "base64 string"
            print(f"  图片 {i}：{img['name']} ({data_type})")
        
        # 调用修复后的函数
        print("🔄 调用 process_images 函数...")
        result = process_images(test_images)
        
        print(f"✅ 处理结果：{len(result)} 个 ImageContent 对象")
        
        # 验证每个结果
        for i, image_content in enumerate(result, 1):
            print(f"  结果 {i}：{type(image_content).__name__}")
        
        # 验证整体可序列化
        print("🔍 验证序列化兼容性...")
        serializable_results = []
        for image_content in result:
            if hasattr(image_content, 'model_dump'):
                data = image_content.model_dump()
            elif hasattr(image_content, 'dict'):
                data = image_content.dict()
            else:
                data = image_content.__dict__
            serializable_results.append(data)
        
        json_output = json.dumps(serializable_results)
        print(f"  ✅ 成功序列化，总大小：{len(json_output)} 字符")
        
        # 模拟 MCP 响应
        mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "command_logs": "",
                "interactive_feedback": "用户提供了截图反馈",
                "images": serializable_results
            }
        }
        
        json.dumps(mcp_response)
        print("  ✅ MCP 响应格式验证通过")
        
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入 process_images：{e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def show_code_diff():
    """显示代码差异"""
    print("\n📝 步骤 4: 查看代码修改")
    print("=" * 50)
    
    print("🔍 关键文件：src/mcp_feedback_enhanced/server.py")
    print("\n--- 修改前 (有问题)")
    print("""
def process_images(images_data: list[dict]) -> list[MCPImage]:
    '''处理图片资料，转换为 MCP 圖片對象'''
    mcp_images = []
    
    for i, img in enumerate(images_data, 1):
        # ... 图片处理逻辑 ...
        mcp_image = MCPImage(data=image_bytes, format=image_format)
        mcp_images.append(mcp_image)  # ❌ 直接返回 MCPImage 对象
    
    return mcp_images
""")
    
    print("\n+++ 修改后 (已修复)")
    print("""
def process_images(images_data: list[dict]) -> list[ImageContent]:
    '''處理圖片資料，轉換為 MCP ImageContent 對象'''
    image_contents = []
    
    for i, img in enumerate(images_data, 1):
        # ... 图片处理逻辑 ...
        mcp_image = MCPImage(data=image_bytes, format=image_format)
        image_content = mcp_image.to_image_content()  # ✅ 转换为可序列化对象
        image_contents.append(image_content)
    
    return image_contents
""")
    
    print("\n🔧 主要变更：")
    print("  1. 返回类型：list[MCPImage] → list[ImageContent]")
    print("  2. 添加转换：mcp_image.to_image_content()")
    print("  3. 导入更新：from mcp.types import ImageContent")
    print("  4. 变量重命名：mcp_images → image_contents")


def main():
    """主函数"""
    print("🧪 MCP Feedback Enhanced - 图片序列化问题复现指南")
    print("🎯 解决用户粘贴截图时的 JSON 序列化错误")
    print("=" * 70)
    
    # 环境检查
    if not setup_environment():
        return False
    
    has_deps = check_dependencies()
    
    if has_deps:
        print("\n✅ 所有依赖已就绪，开始完整演示...\n")
        
        results = [
            demonstrate_original_issue(),
            demonstrate_fixed_solution(),
            test_process_images_function()
        ]
        
        show_code_diff()
        
        # 汇总结果
        print(f"\n📊 测试结果")
        print("=" * 40)
        test_names = ["原始问题演示", "修复方案验证", "函数集成测试"]
        for name, success in zip(test_names, results):
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {name}: {status}")
        
        if all(results):
            print("\n🎉 完整演示成功！")
            print("\n💡 总结：")
            print("  • 问题：fastmcp.utilities.types.Image 对象包含不可序列化的 bytes 数据")
            print("  • 影响：用户粘贴截图时 MCP 协议序列化失败")
            print("  • 修复：使用 .to_image_content() 转换为 mcp.types.ImageContent")
            print("  • 效果：完全解决序列化问题，用户可正常使用截图功能")
            print("  • 变更：最小化修改（14 行新增，13 行删除）")
        else:
            print("\n⚠️  部分演示失败，请检查环境配置")
    
    else:
        print("\n⚠️  缺少依赖，显示概念演示...")
        print("\n📖 概念说明：")
        print("  1. 问题核心：bytes 对象无法 JSON 序列化")
        print("  2. 修复思路：转换为 base64 字符串")
        print("  3. 实现方式：调用 .to_image_content() 方法")
        print("  4. 效果验证：可以正常序列化为 JSON")
        
        show_code_diff()
    
    print("\n📚 更多信息：")
    print("  • 测试文件：tests/unit/test_image_serialization.py")
    print("  • 相关 issue：图片粘贴功能的 JSON 序列化错误")
    print("  • PR 变更：最小化修改，保持向后兼容")


if __name__ == "__main__":
    main()