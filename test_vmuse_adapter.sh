#!/bin/bash
#
# VMUSE 适配器测试脚本
# 
# 用途：快速验证 VMUSE 适配器功能
#

set -e

echo "=========================================="
echo "VMUSE 适配器测试"
echo "=========================================="
echo ""

# 检查目录
if [ ! -d "novaic-backend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

cd novaic-backend

# 1. 检查文件存在
echo "📋 1. 检查文件完整性..."
files=(
    "gateway/clients/vmuse_adapter.py"
    "gateway/clients/vmuse_adapter_example.py"
    "tests/unit/gateway/test_vmuse_adapter.py"
    "common/config.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file 不存在"
        exit 1
    fi
done

echo ""

# 2. 运行单元测试
echo "🧪 2. 运行单元测试..."
echo ""

if command -v pytest &> /dev/null; then
    python -m pytest tests/unit/gateway/test_vmuse_adapter.py -v --tb=short
    if [ $? -eq 0 ]; then
        echo ""
        echo "  ✅ 所有测试通过"
    else
        echo ""
        echo "  ❌ 测试失败"
        exit 1
    fi
else
    echo "  ⚠️  pytest 未安装，跳过测试"
fi

echo ""

# 3. 检查语法
echo "🔍 3. 检查语法..."
python -m py_compile gateway/clients/vmuse_adapter.py
if [ $? -eq 0 ]; then
    echo "  ✅ 语法检查通过"
else
    echo "  ❌ 语法错误"
    exit 1
fi

echo ""

# 4. 检查导入
echo "📦 4. 检查导入..."
python -c "from gateway.clients.vmuse_adapter import get_vmuse_adapter; print('  ✅ 导入成功')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  ❌ 导入失败"
    exit 1
fi

echo ""

# 5. 检查配置
echo "⚙️  5. 检查配置..."
python -c "from common.config import ServiceConfig; print(f'  USE_LEGACY_VMUSE: {ServiceConfig.USE_LEGACY_VMUSE}'); print(f'  VMCONTROL_URL: {ServiceConfig.VMCONTROL_URL}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  ❌ 配置检查失败"
    exit 1
fi

echo ""

# 6. 显示统计
echo "📊 6. 代码统计..."
echo ""
echo "  文件数量："
echo "    - 实现: $(find gateway/clients -name "*vmuse*" -type f | wc -l | xargs)"
echo "    - 测试: $(find tests -name "*vmuse*" -type f | wc -l | xargs)"
echo ""
echo "  代码行数："
wc -l gateway/clients/vmuse_adapter.py gateway/clients/vmuse_adapter_example.py tests/unit/gateway/test_vmuse_adapter.py 2>/dev/null | tail -1

echo ""

# 7. 运行示例（可选）
echo "💡 7. 运行示例（可选）..."
echo ""
echo "  如需运行示例，请执行："
echo "  python -m gateway.clients.vmuse_adapter_example --example compat"
echo ""

# 总结
echo "=========================================="
echo "✅ VMUSE 适配器验证完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 查看快速参考: cat ../VMUSE_ADAPTER_QUICK_REF.md"
echo "  2. 阅读迁移指南: cat ../VMUSE_MIGRATION_GUIDE.md"
echo "  3. 运行示例代码: python -m gateway.clients.vmuse_adapter_example"
echo ""
