# 图片序列化问题复现和测试指南

这个目录包含了用于复现和验证 MCP Feedback Enhanced 图片序列化问题修复的文件。

## 问题描述

当用户在 MCP Feedback Enhanced Web UI 中粘贴截图时，系统会抛出 JSON 序列化错误：

```
Unable to serialize unknown type: <class 'fastmcp.utilities.types.Image'>
```

## 根本原因

`process_images` 函数返回的 `fastmcp.utilities.types.Image` 对象包含 `bytes` 类型的数据，无法被 JSON 序列化，导致 MCP 协议响应失败。

## 修复方案

使用 `.to_image_content()` 方法将 `Image` 对象转换为 `mcp.types.ImageContent` 对象：

```python
# 修改前（有问题）
mcp_image = MCPImage(data=image_bytes, format=image_format)
mcp_images.append(mcp_image)

# 修改后（已修复）
mcp_image = MCPImage(data=image_bytes, format=image_format)
image_content = mcp_image.to_image_content()
image_contents.append(image_content)
```

## 文件说明

### 1. `reproduction_guide.py`
完整的复现和演示脚本，包含：
- 环境检查和依赖验证
- 原始问题演示
- 修复方案验证
- 函数集成测试
- 代码对比展示

### 2. `test_image_serialization.py`
单元测试文件，包含：
- `process_images` 函数的序列化测试
- `ImageContent` 对象结构验证
- 序列化问题的概念验证
- 边界情况测试

## 运行方法

### 完整演示（需要依赖）
```bash
# 1. 安装依赖
pip install -e .

# 2. 运行完整演示
python examples/reproduction_guide.py
```

### 概念演示（无需依赖）
```bash
# 直接运行，会显示概念说明和代码对比
python examples/reproduction_guide.py
```

### 运行测试
```bash
# 运行序列化相关测试
pytest tests/unit/test_image_serialization.py -v

# 运行所有测试
pytest tests/ -v
```

## 复现步骤

1. **用户操作**：用户在 Web UI 中粘贴截图
2. **数据传输**：前端发送 base64 编码的图片数据到后端
3. **后端处理**：`process_images` 函数创建 `Image` 对象
4. **序列化失败**：MCP 协议尝试序列化响应时失败
5. **用户影响**：用户看到错误，无法提交图片反馈

## 验证修复效果

修复后的流程：

1. **数据处理**：同样的图片数据处理逻辑
2. **对象转换**：调用 `.to_image_content()` 转换对象
3. **成功序列化**：`ImageContent` 对象可以正常序列化
4. **用户体验**：用户可以正常粘贴和提交截图

## 技术细节

### 序列化问题的核心
```python
# 问题：bytes 对象无法 JSON 序列化
image_data = b'\x89PNG\r\n\x1a\n...'  # bytes
json.dumps({"data": image_data})  # TypeError: Object of type bytes is not JSON serializable

# 解决：转换为 base64 字符串
image_data_b64 = base64.b64encode(image_data).decode()  # str
json.dumps({"data": image_data_b64})  # 成功
```

### ImageContent 对象结构
```json
{
  "type": "image",
  "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "format": "png"
}
```

## 变更摘要

- **文件**：`src/mcp_feedback_enhanced/server.py`
- **函数**：`process_images`
- **变更**：14 行新增，13 行删除
- **影响**：完全解决序列化问题，无破坏性变更
- **兼容性**：保持向后兼容，现有功能不受影响