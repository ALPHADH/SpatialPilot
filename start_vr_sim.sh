#!/bin/bash
# ============================================================
#  Fast-Drone-250 VR仿真启动脚本
#  Quest VR头显 -> 控制仿真无人机飞行
# ============================================================

set -e

CONTAINER="fast-drone-250"
IMAGE="osrf/ros:noetic-desktop-full"
WORKSPACE="/home/dh/桌面/bishe/Fast-Drone-250-master"
LAUNCH_PKG="quest2ros"
LAUNCH_FILE="quest_sim.launch"

# ---------- 1. 确保Docker容器运行 ----------
echo "[1/5] 检查 Docker 容器..."
if sg docker -c "docker ps -q -f name=$CONTAINER" 2>/dev/null | grep -q .; then
    echo "  -> 容器已在运行"
else
    echo "  -> 启动容器..."
    xhost +local: > /dev/null 2>&1
    XAUTH=$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
    if [ -z "$XAUTH" ]; then
        XAUTH="$HOME/.Xauthority"
    fi
    sg docker -c "docker rm -f $CONTAINER" 2>/dev/null || true
    sg docker -c "docker run -d \
        --name $CONTAINER \
        --network host \
        -e DISPLAY=\$DISPLAY \
        -e XAUTHORITY=/tmp/.Xauthority \
        -e QT_X11_NO_MITSHM=1 \
        -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
        -v $XAUTH:/tmp/.Xauthority:ro \
        -v $WORKSPACE:/workspace \
        -w /workspace \
        $IMAGE sleep infinity"

    # 修复 python -> python3 软链接
    sg docker -c "docker exec $CONTAINER bash -c 'ln -sf /usr/bin/python3 /usr/bin/python 2>/dev/null'"

    echo "  -> 容器已启动"
fi

# ---------- 2. X11授权 ----------
echo "[2/5] 配置 X11 授权..."
xhost +local: > /dev/null 2>&1
echo "  -> 完成"

# ---------- 3. 清理旧仿真 ----------
echo "[3/5] 清理旧仿真进程..."
sg docker -c "docker exec $CONTAINER bash -c 'killall -9 roslaunch rosout rviz 2>/dev/null; sleep 1' || true"
echo "  -> 完成"

# ---------- 4. 启动VR仿真 ----------
echo "[4/5] 启动 VR 无人机仿真..."
sg docker -c "docker exec $CONTAINER bash -c '
    source /opt/ros/noetic/setup.bash
    source /workspace/devel/setup.bash
    nohup roslaunch $LAUNCH_PKG $LAUNCH_FILE > /tmp/vr_sim.log 2>&1 &
'"

sleep 6
echo ""
echo "========================================"
echo "  VR仿真已启动!"
echo "========================================"
echo ""
echo "  ┌─────────────────────────────────────┐"
echo "  │  使用流程                           │"
echo "  ├─────────────────────────────────────┤"
echo "  │  1. Windows端: 建立SSH隧道 (双端口)                  │"
echo "  │     ssh -N -L 0.0.0.0:10000:... -L 0.0.0.0:8888:... │"
echo "  │  2. Quest2ROS App: WiFi-IP:10000  控制无人机         │"
echo "  │  3. Quest浏览器:   WiFi-IP:8888   飞行仪表盘         │"
echo "  │  4. 右手食指扳机 = 发送目标点                        │"
echo "  │  5. 键盘控制 (可选): 新终端运行下面命令              │"
echo "  ├─────────────────────────────────────┤"
echo "  │  停止仿真: ./stop_sim.sh                             │"
echo "  └─────────────────────────────────────┘"
echo ""
echo "  键盘控制节点 (H=复位 Q=退出):"
echo "    sg docker -c 'docker exec -it $CONTAINER bash -c \"
echo "      source /opt/ros/noetic/setup.bash && \"
echo "      source /workspace/devel/setup.bash && \"
echo "      rosrun quest2ros keyboard_control.py\"'"
echo ""

# ---------- 5. 显示连接日志 ----------
echo "[5/5] 等待 VR 连接..."
sleep 3
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "  PC IP: $IP"
echo "  TCP Endpoint: tcp://$IP:10000"
echo ""
echo "  [VR Bridge]: $(sg docker -c "docker exec $CONTAINER bash -c 'grep -c \"Ready\" /tmp/vr_sim.log 2>/dev/null || echo waiting'" 2>/dev/null)"
echo ""
echo "  当Quest连接后，bridge日志会显示 'Goal sent'"
echo "  查看实时日志:"
echo "    sg docker -c 'docker exec $CONTAINER tail -f /tmp/vr_sim.log'"
echo ""
