---
name: novaic-files
description: File system operations including reading, writing, and listing files. Use for file manipulation and content management.
---

# File Operations

文件系统操作工具。

## 可用工具

### read_file

读取文件内容。

```python
# 读取文件
read_file(path="/path/to/file.txt")

# 注意：大文件会被截断，返回 result_id
# 使用 result_get 获取完整内容
```

### write_file

写入文件，自动创建目录。

```python
# 写入文件
write_file(path="/path/to/file.txt", content="Hello World")

# 自动创建父目录
write_file(path="/new/dir/file.txt", content="Content")
```

### list_files

列出目录内容（类似 ls -la）。

```python
# 列出当前目录
list_files()

# 列出指定目录
list_files(path="/path/to/dir")
```

### file_info

获取文件元信息。

```python
file_info(path="/path/to/file")
# 返回:
# - 文件大小
# - 类型
# - 权限
# - 创建/修改时间
```

## 结果缓存

当输出被截断时，会返回 `result_id`：

```python
# 读取大文件
result = read_file(path="large_file.txt")
# 返回: {"truncated": true, "result_id": "xxx", ...}

# 按行获取完整内容
result_get(result_id="xxx", start_line=1, end_line=100)

# 按字符获取
result_get(result_id="xxx", start_char=0, length=5000, mode="chars")

# 查看缓存信息
result_info(result_id="xxx")

# 列出所有缓存
result_list()
```

## 常见用例

### 读取配置文件

```python
# 读取 JSON 配置
content = read_file(path="config.json")

# 读取环境变量
content = read_file(path=".env")
```

### 写入代码文件

```python
# 创建 Python 文件
write_file(
    path="src/utils.py",
    content='''
def helper():
    return "Hello"
'''
)
```

### 项目文件列表

```python
# 列出项目根目录
list_files(path=".")

# 查看 src 目录
list_files(path="src")
```

## 最佳实践

1. **读取前检查**：使用 `list_files()` 确认文件存在
2. **大文件处理**：注意截断，使用 `result_get()` 获取完整内容
3. **路径使用**：优先使用绝对路径
