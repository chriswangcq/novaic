#!/bin/bash
# VMUSE 部署脚本 - 自动部署到 VM
# 使用方法: ./deploy_vmuse_to_vm.sh [VM_ID]

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VMUSE 自动部署到 VM${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查 VM ID
if [ -z "$1" ]; then
    echo -e "${YELLOW}获取 VM 列表...${NC}"
    VM_LIST=$(curl -s http://localhost:8080/api/vms | python3 -m json.tool)
    echo "$VM_LIST"
    
    VM_ID=$(echo "$VM_LIST" | python3 -c "import sys, json; vms=json.load(sys.stdin); print(vms[0]['id'] if vms else '')")
    
    if [ -z "$VM_ID" ]; then
        echo -e "${RED}❌ 没有找到运行中的 VM${NC}"
        echo "请先启动 VM，然后使用: $0 VM_ID"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 使用 VM: $VM_ID${NC}"
else
    VM_ID="$1"
    echo -e "${GREEN}✓ VM ID: $VM_ID${NC}"
fi

# 1. 打包代码
echo -e "\n${YELLOW}[1/5] 打包 VMUSE 代码...${NC}"
cd "$(dirname "$0")"
tar czf /tmp/novaic-mcp-vmuse.tar.gz -C novaic-app/src-tauri/resources novaic-mcp-vmuse
echo -e "${GREEN}✓ 打包完成: $(ls -lh /tmp/novaic-mcp-vmuse.tar.gz | awk '{print $5}')${NC}"

# 2. 上传到 VM
echo -e "\n${YELLOW}[2/5] 上传到 VM...${NC}"
python3 << EOPY
import requests
import base64

vm_id = "$VM_ID"

with open('/tmp/novaic-mcp-vmuse.tar.gz', 'rb') as f:
    tar_content = f.read()

print(f"  文件大小: {len(tar_content):,} bytes")

tar_b64 = base64.b64encode(tar_content).decode('utf-8')

response = requests.post(
    f"http://localhost:8080/api/vms/{vm_id}/guest/file",
    json={"path": "/tmp/novaic-mcp-vmuse.tar.gz", "content": tar_b64},
    timeout=120
)

result = response.json()
if result.get('success'):
    print(f"  ✓ 上传成功: {result.get('bytes_written', 0):,} bytes")
else:
    print(f"  ✗ 上传失败: {result.get('error', 'Unknown error')}")
    exit(1)
EOPY

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 上传失败${NC}"
    exit 1
fi

# 3. 解压并安装
echo -e "\n${YELLOW}[3/5] 在 VM 内解压并安装...${NC}"
curl -s -X POST "http://localhost:8080/api/vms/$VM_ID/guest/exec" \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "/bin/bash",
    "args": ["-c", "cd /opt/novaic && rm -rf novaic-mcp-vmuse && tar xzf /tmp/novaic-mcp-vmuse.tar.gz && cd novaic-mcp-vmuse && pip install -q -e . && echo Installation complete"],
    "wait": true
  }' | python3 -c "import sys, json, base64; d=json.load(sys.stdin); out=base64.b64decode(d.get('stdout','')).decode('utf-8') if d.get('stdout') else ''; print(out); exit(0 if d.get('exit_code')==0 else 1)"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 安装失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 安装完成${NC}"

# 4. 创建 systemd 服务
echo -e "\n${YELLOW}[4/5] 创建 systemd 服务...${NC}"
curl -s -X POST "http://localhost:8080/api/vms/$VM_ID/guest/exec" \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "/bin/bash",
    "args": ["-c", "sudo tee /etc/systemd/system/novaic-vmuse.service > /dev/null <<'\''UNIT'\''\n[Unit]\nDescription=NovAIC VMUSE HTTP Server\nAfter=network.target\n\n[Service]\nType=simple\nUser=ubuntu\nWorkingDirectory=/opt/novaic/novaic-mcp-vmuse\nEnvironment=\"PYTHONPATH=/opt/novaic/novaic-mcp-vmuse/src\"\nEnvironment=\"DISPLAY=:0\"\nExecStart=/usr/bin/python3 -m novaic_mcp_vmuse.http_server\nRestart=always\nRestartSec=3\n\n[Install]\nWantedBy=multi-user.target\nUNIT\nsudo systemctl daemon-reload && sudo systemctl enable novaic-vmuse && sudo systemctl restart novaic-vmuse && sleep 2 && systemctl status novaic-vmuse --no-pager"],
    "wait": true
  }' | python3 -c "import sys, json; d=json.load(sys.stdin); print('  服务状态:', '运行中' if d.get('exit_code')==0 else '失败'); exit(0 if d.get('exit_code')==0 else 1)"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 服务创建失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 服务已启动${NC}"

# 5. 验证
echo -e "\n${YELLOW}[5/5] 验证部署...${NC}"

# 健康检查
echo -n "  健康检查: "
curl -s -X POST "http://localhost:8080/api/vms/$VM_ID/vmuse/shell/run_command" \
  -H 'Content-Type: application/json' \
  -d '{"command":"curl -s http://localhost:8080/health"}' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); data=d.get('data',{}); stdout=data.get('stdout',''); print('✓ 服务正常' if 'healthy' in stdout else '✗ 服务异常')"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "测试命令:"
echo "  # 截图"
echo "  curl -X POST 'http://localhost:8080/api/vms/$VM_ID/vmuse/desktop/screenshot' \\"
echo "    -H 'Content-Type: application/json' -d '{\"area\":\"full\",\"grid\":true}'"
echo ""
echo "  # Shell 命令"
echo "  curl -X POST 'http://localhost:8080/api/vms/$VM_ID/vmuse/shell/run_command' \\"
echo "    -H 'Content-Type: application/json' -d '{\"command\":\"uname -a\"}'"
echo ""
echo "查看服务日志:"
echo "  curl -X POST 'http://localhost:8080/api/vms/$VM_ID/guest/exec' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"path\":\"/bin/bash\",\"args\":[\"-c\",\"journalctl -u novaic-vmuse -n 50\"],\"wait\":true}'"
