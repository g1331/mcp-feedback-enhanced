#!/usr/bin/env python3
"""
圖片序列化單元測試

測試 process_images 函數的圖片處理和序列化功能，
確保修復了 JSON 序列化錯誤問題。

問題描述：
- 原始問題：process_images 返回 fastmcp.utilities.types.Image 對象，無法 JSON 序列化
- 修復方案：轉換為 mcp.types.ImageContent 對象，可以正常序列化
"""

import base64
import json
from unittest.mock import patch

import pytest

from mcp_feedback_enhanced.server import process_images


class TestImageSerialization:
    """圖片序列化測試類"""

    def test_process_images_returns_image_content_objects(self):
        """測試 process_images 返回 ImageContent 對象而不是 Image 對象"""
        # 創建測試圖片數據（1x1 PNG 像素）
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        images_data = [
            {
                "data": base64.b64encode(png_data).decode(),
                "name": "test.png"
            }
        ]
        
        # 調用 process_images
        result = process_images(images_data)
        
        # 驗證返回類型
        assert isinstance(result, list)
        assert len(result) == 1
        
        # 驗證返回的是 ImageContent 對象，而不是 Image 對象
        from mcp.types import ImageContent
        assert isinstance(result[0], ImageContent)
        
        # 驗證對象有正確的屬性
        image_content = result[0]
        assert hasattr(image_content, "type")
        assert image_content.type == "image"
        assert hasattr(image_content, "data")
        assert hasattr(image_content, "mimeType")

    def test_image_content_objects_are_json_serializable(self):
        """測試返回的 ImageContent 對象可以被 JSON 序列化"""
        # 創建測試圖片數據
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        images_data = [
            {
                "data": base64.b64encode(png_data).decode(),
                "name": "test.png"
            }
        ]
        
        # 調用 process_images
        result = process_images(images_data)
        
        # 嘗試 JSON 序列化 - 這應該成功
        try:
            serialized = json.dumps(result, default=lambda obj: obj.__dict__)
            # 驗證序列化成功
            assert isinstance(serialized, str)
            assert len(serialized) > 0
        except TypeError as e:
            pytest.fail(f"ImageContent 對象無法序列化: {e}")

    def test_original_problem_would_fail_with_image_objects(self):
        """測試原始問題：如果返回 Image 對象會導致序列化失敗
        
        這個測試模擬原始的 bug 情況，證明 fastmcp.utilities.types.Image 
        對象確實無法被 JSON 序列化
        """
        from fastmcp.utilities.types import Image as MCPImage
        
        # 創建測試圖片數據
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        # 創建 MCPImage 對象（原始的返回類型）
        mcp_image = MCPImage(data=png_data, format="png")
        
        # 嘗試序列化 - 這應該失敗
        with pytest.raises((TypeError, ValueError, AttributeError)) as exc_info:
            json.dumps([mcp_image])
        
        # 驗證錯誤類型或內容
        error_msg = str(exc_info.value).lower()
        assert ("not json serializable" in error_msg or 
                "not serializable" in error_msg or 
                "object of type" in error_msg or
                "bytes" in error_msg)

    def test_process_images_handles_multiple_image_formats(self):
        """測試 process_images 處理多種圖片格式"""
        # 測試數據（1x1 像素圖片）
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        images_data = [
            {"data": base64.b64encode(png_data).decode(), "name": "test.png"},
            {"data": base64.b64encode(png_data).decode(), "name": "test.jpg"},
            {"data": base64.b64encode(png_data).decode(), "name": "test.gif"},
        ]
        
        result = process_images(images_data)
        
        assert len(result) == 3
        
        # 所有結果都應該是 ImageContent 對象
        from mcp.types import ImageContent
        for image_content in result:
            assert isinstance(image_content, ImageContent)
            assert image_content.type == "image"

    def test_process_images_handles_bytes_data(self):
        """測試 process_images 處理原始 bytes 數據"""
        # 創建測試圖片數據
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        images_data = [
            {
                "data": png_data,  # 直接使用 bytes
                "name": "test.png"
            }
        ]
        
        result = process_images(images_data)
        
        assert len(result) == 1
        from mcp.types import ImageContent
        assert isinstance(result[0], ImageContent)

    def test_process_images_handles_empty_or_invalid_data(self):
        """測試 process_images 處理空或無效數據"""
        # 測試空列表
        result = process_images([])
        assert result == []
        
        # 測試無效數據
        images_data = [
            {"data": "", "name": "empty.png"},  # 空數據
            {"name": "no_data.png"},  # 沒有數據字段
            {"data": None, "name": "none_data.png"},  # None 數據
        ]
        
        result = process_images(images_data)
        # 應該跳過無效數據，返回空列表
        assert result == []

    @patch('mcp_feedback_enhanced.server.debug_log')
    def test_process_images_logs_processing_info(self, mock_debug_log):
        """測試 process_images 記錄處理信息"""
        # 創建測試圖片數據
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        images_data = [
            {
                "data": base64.b64encode(png_data).decode(),
                "name": "test.png"
            }
        ]
        
        result = process_images(images_data)
        
        # 驗證調用了調試日誌
        assert mock_debug_log.called
        # 驗證記錄了處理成功的信息
        log_calls = [str(call) for call in mock_debug_log.call_args_list]
        assert any("處理成功" in call for call in log_calls)
        assert any("共處理" in call for call in log_calls)