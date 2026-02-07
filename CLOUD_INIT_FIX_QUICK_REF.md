# Cloud-Init 修复 - 快速参考

**日期**: 2026-02-07  
**状态**: ✅ 完成

---

## 修改内容

### 文件: `novaic-backend/gateway/vm/setup.py`

#### 1. 删除 write_files 的 owner 字段 (Line 665)
```diff
      if __name__ == "__main__":
          main()
    permissions: '0755'
-   owner: ubuntu:ubuntu
```

#### 2. 使用虚拟环境安装 Playwright (Line 667-707)
```diff
  runcmd:
-   # Set up directory permissions
-   - chown -R ubuntu:ubuntu /home/ubuntu
+   # Set up directory structure first (ubuntu user now exists)
    - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
    - mkdir -p /opt/novaic/scripts
-   - chown -R ubuntu:ubuntu /opt/novaic
+   - mkdir -p /opt/novaic/venv
    
    ...
    
-   # Install Playwright and Chromium (as ubuntu user)
-   - echo "Installing Playwright..."
-   - sudo -u ubuntu pip3 install --user playwright
-   - sudo -u ubuntu python3 -m playwright install chromium
-   - sudo -u ubuntu python3 -m playwright install-deps chromium
-   - echo "Playwright installation completed."
+   # Install Playwright using virtual environment (PEP 668 compliance)
+   - echo "Creating Python virtual environment..."
+   - python3 -m venv /opt/novaic/venv
+   - echo "Installing Playwright in virtual environment..."
+   - /opt/novaic/venv/bin/pip install --upgrade pip
+   - /opt/novaic/venv/bin/pip install playwright
+   - echo "Installing Chromium browser..."
+   - /opt/novaic/venv/bin/playwright install --with-deps chromium
+   - echo "Playwright installation completed."
+   
+   # Update playwright_helper.py shebang to use virtual environment
+   - sed -i '1s|.*|#!/opt/novaic/venv/bin/python3|' /opt/novaic/scripts/playwright_helper.py
+   
+   # Set correct ownership (now that ubuntu user exists)
+   - chown -R ubuntu:ubuntu /home/ubuntu
+   - chown -R ubuntu:ubuntu /opt/novaic
```

---

## 解决的问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 时序问题 | write_files 在 ubuntu 用户创建前执行 | 移除 owner 字段，在 runcmd 中设置权限 |
| PEP 668 | Ubuntu 24.04 禁止直接 pip install | 使用 Python 虚拟环境 `/opt/novaic/venv` |
| Shebang 错误 | playwright_helper.py 使用系统 Python | 自动更新为虚拟环境 Python |

---

## 验证

```bash
# 语法检查
python3 -m py_compile novaic-backend/gateway/vm/setup.py  # ✅ 通过

# 下次创建 VM 时自动生效
# 无需额外操作
```

---

## 执行顺序

```
1. packages → python3-venv
2. users → ubuntu 用户创建
3. write_files → playwright_helper.py (无 owner)
4. runcmd →
   ├─ 创建目录
   ├─ 创建虚拟环境
   ├─ 安装 Playwright
   ├─ 更新 shebang
   └─ 设置权限 ✅
```

---

## 测试命令

```bash
# VM 内验证
ssh ubuntu@<vm-ip>

# 检查虚拟环境
ls -la /opt/novaic/venv/bin/python3

# 检查 Playwright
/opt/novaic/venv/bin/playwright --version

# 测试 playwright_helper
/opt/novaic/scripts/playwright_helper.py screenshot
```

---

**修复完成** ✅ **下次创建 VM 自动生效**
