#!/bin/bash
# ============================================================
#  Fast-Drone-250 仿真停止脚本
#  停止VR仿真、清理Docker容器、恢复终端设置
# ============================================================

set -e

CONTAINER="fast-drone-250"

echo "========================================"
echo "  停止 Fast-Drone-250 仿真"
echo "========================================"

# ---------- 1. 停止ROS仿真进程 ----------
echo "[1/3] 停止 ROS 仿真进程..."
if sg docker -c "docker ps -q -f name=$CONTAINER" 2>/dev/null | grep -q .; then
    sg docker -c "docker exec $CONTAINER bash -c 'killall -9 roslaunch rosout rviz rosmaster 2>/dev/null; sleep 1' || true"
    echo "  -> 已停止"
else
    echo "  -> 容器未运行，跳过"
fi

# ---------- 2. 可选：停止Docker容器 ----------
echo "[2/3] 清理容器..."
if sg docker -c "docker ps -q -f name=$CONTAINER" 2>/dev/null | grep -q .; then
    read -p "  是否停止Docker容器? [y/N]: " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sg docker -c "docker rm -f $CONTAINER"
        echo "  -> 容器已移除"
    else
        echo "  -> 保留容器（仅停止了ROS进程）"
    fi
else
    echo "  -> 容器未运行"
fi

# ---------- 3. 清理X11授权 ----------
echo "[3/3] 清理 X11 授权..."
xhost -local: > /dev/null 2>&1 || true
echo "  -> 完成"

echo ""
echo "========================================"
echo "  仿真已停止"
echo "========================================"
echo ""
echo "  下次启动:"
echo "    ./start_vr_sim.sh                # 启动VR仿真"
echo "    ./connect_quest.bat  (Windows)   # 建立Quest连接隧道"
echo ""
