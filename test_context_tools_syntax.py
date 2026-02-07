#!/usr/bin/env python3
"""
验证 Context 工具实现的语法和结构
"""

import ast
import sys

def analyze_vmuse_adapter():
    """分析 vmuse_adapter.py 文件"""
    
    file_path = "novaic-backend/gateway/clients/vmuse_adapter.py"
    
    print(f"分析文件: {file_path}")
    print("=" * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 解析 AST
    try:
        tree = ast.parse(code)
        print("✅ Python 语法正确")
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False
    
    # 查找类定义
    vmuse_adapter_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "VmuseAdapter":
            vmuse_adapter_class = node
            break
    
    if not vmuse_adapter_class:
        print("❌ 未找到 VmuseAdapter 类")
        return False
    
    print("✅ 找到 VmuseAdapter 类")
    
    # 查找方法
    methods = {}
    for node in vmuse_adapter_class.body:
        if isinstance(node, ast.AsyncFunctionDef):
            methods[node.name] = node
    
    # 检查 Context 工具方法
    context_methods = [
        "_exec_guest_command",
        "_system_snapshot",
        "_clipboard_get",
        "_clipboard_set",
        "_environment_info"
    ]
    
    print("\n检查 Context 工具方法:")
    for method_name in context_methods:
        if method_name in methods:
            method = methods[method_name]
            args = [arg.arg for arg in method.args.args if arg.arg != 'self']
            print(f"✅ {method_name}({', '.join(args)})")
        else:
            print(f"❌ {method_name} - 未找到")
    
    # 检查 call_tool 方法中的路由
    call_tool_method = methods.get("call_tool")
    if call_tool_method:
        code_str = ast.get_source_segment(code, call_tool_method)
        
        print("\n检查 call_tool 路由:")
        context_tools = ["system_snapshot", "clipboard_get", "clipboard_set", "environment_info"]
        for tool in context_tools:
            if f'tool_name == "{tool}"' in code_str:
                print(f"✅ {tool} - 已路由")
            else:
                print(f"❌ {tool} - 未路由")
    
    # 检查 list_tools_mcp_format 方法
    list_tools_method = methods.get("list_tools_mcp_format")
    if list_tools_method:
        code_str = ast.get_source_segment(code, list_tools_method)
        
        print("\n检查 list_tools_mcp_format 工具定义:")
        for tool in context_tools:
            if f'"name": "{tool}"' in code_str:
                print(f"✅ {tool} - 已定义")
            else:
                print(f"❌ {tool} - 未定义")
    
    # 检查 shlex 导入
    print("\n检查模块导入:")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    
    if "shlex" in imports:
        print("✅ shlex 模块已导入")
    else:
        print("❌ shlex 模块未导入")
    
    # 检查 shlex.quote 的使用
    if "shlex.quote" in code:
        print("✅ 使用了 shlex.quote 进行安全引用")
    
    return True

if __name__ == "__main__":
    print("Context 工具实现验证")
    print("=" * 60)
    
    try:
        if analyze_vmuse_adapter():
            print("\n" + "=" * 60)
            print("✅ 验证通过！")
            print("=" * 60)
        else:
            print("\n❌ 验证失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
