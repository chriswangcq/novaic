#!/bin/bash
# NovAIC Backend - 完整开发模式启动脚本
# 按正确顺序启动所有后端服务

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== NovAIC Backend 开发模式启动 =====${NC}\n"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}错误: 找不到 venv 虚拟环境${NC}"
    echo "请先运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 设置数据目录
export NOVAIC_DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"
export NO_PROXY="localhost,127.0.0.1,::1"
export no_proxy="localhost,127.0.0.1,::1"

echo -e "${GREEN}数据目录: $NOVAIC_DATA_DIR${NC}\n"

# 创建日志目录
mkdir -p "$NOVAIC_DATA_DIR/logs"

# 清理旧进程
echo "清理旧进程..."
pkill -f "novaic_main" 2>/dev/null || true
sleep 2

# 1. 启动 Gateway
echo -e "${GREEN}[1/10] 启动 Gateway (19999)...${NC}"
nohup python -m novaic_main gateway --port 19999 --data-dir "$NOVAIC_DATA_DIR" \
    > "$NOVAIC_DATA_DIR/logs/gateway-dev.log" 2>&1 &
sleep 3

# 2. 启动 Queue Service
echo -e "${GREEN}[2/10] 启动 Queue Service (19997)...${NC}"
nohup python -m novaic_main queue-service --port 19997 --data-dir "$NOVAIC_DATA_DIR" \
    > "$NOVAIC_DATA_DIR/logs/queue-dev.log" 2>&1 &
sleep 2

# 3. 启动 Tools Server
echo -e "${GREEN}[3/10] 启动 Tools Server (19998)...${NC}"
nohup python -m novaic_main tools-server --port 19998 --data-dir "$NOVAIC_DATA_DIR" --gateway-url http://127.0.0.1:19999 \
    > "$NOVAIC_DATA_DIR/logs/tools-dev.log" 2>&1 &
sleep 2

# 4. 启动 File Service
echo -e "${GREEN}[4/10] 启动 File Service (19995)...${NC}"
nohup python -m file_service.main --port 19995 --base-dir "$NOVAIC_DATA_DIR" \
    > "$NOVAIC_DATA_DIR/logs/file-service-dev.log" 2>&1 &
sleep 2

# 5. 启动 Tool Result Service (TRS)
echo -e "${GREEN}[5/10] 启动 Tool Result Service (19994)...${NC}"
nohup python -m tool_result_service.main --port 19994 \
    > "$NOVAIC_DATA_DIR/logs/trs-dev.log" 2>&1 &
sleep 2

# 等待核心服务就绪
echo "等待核心服务就绪..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:19999/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Gateway 就绪${NC}"
        break
    fi
    sleep 1
done

# 6. 启动 Watchdog
echo -e "${GREEN}[6/10] 启动 Watchdog...${NC}"
nohup python -m novaic_main watchdog --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 \
    > "$NOVAIC_DATA_DIR/logs/watchdog-dev.log" 2>&1 &
sleep 1

# 7. 启动 Task Workers (3个)
echo -e "${GREEN}[7/10] 启动 Task Workers (3个)...${NC}"
for i in {1..3}; do
    nohup python -m novaic_main task-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 \
        > "$NOVAIC_DATA_DIR/logs/task-worker-$i-dev.log" 2>&1 &
    sleep 0.5
done

# 8. 启动 Saga Workers (3个)
echo -e "${GREEN}[8/10] 启动 Saga Workers (3个)...${NC}"
for i in {1..3}; do
    nohup python -m novaic_main saga-worker --gateway-url http://127.0.0.1:19999 --queue-service-url http://127.0.0.1:19997 \
        > "$NOVAIC_DATA_DIR/logs/saga-worker-$i-dev.log" 2>&1 &
    sleep 0.5
done

# 9. 启动 Health Worker
echo -e "${GREEN}[9/10] 启动 Health Worker...${NC}"
nohup python -m novaic_main health --queue-service-url http://127.0.0.1:19997 \
    > "$NOVAIC_DATA_DIR/logs/health-dev.log" 2>&1 &
sleep 1

# 10. 启动 Scheduler
echo -e "${GREEN}[10/10] 启动 Scheduler...${NC}"
nohup python -m novaic_main scheduler --gateway-url http://127.0.0.1:19999 \
    > "$NOVAIC_DATA_DIR/logs/scheduler-dev.log" 2>&1 &
sleep 1

echo -e "\n${GREEN}===== 所有服务启动完成 =====${NC}\n"

# 显示进程状态
echo "运行中的进程："
ps aux | grep -E "(gateway|tools_server|queue_service|file_service|tool_result|watchdog|task-worker|saga-worker|health|scheduler)" | grep python | grep -v grep | awk '{print $2, $11, $12, $13, $14, $15}'

echo -e "\n日志文件位置: $NOVAIC_DATA_DIR/logs/"
echo -e "\n服务健康检查:"
echo "  Gateway:     curl http://127.0.0.1:19999/api/health"
echo "  Queue:       curl http://127.0.0.1:19997/api/health"  
echo "  Tools:       curl http://127.0.0.1:19998/api/health"
echo "  File:        curl http://127.0.0.1:19995/api/health"
echo "  TRS:         curl http://127.0.0.1:19994/api/health"

echo -e "\n停止所有服务: pkill -f novaic_main"
