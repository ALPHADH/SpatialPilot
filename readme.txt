Fast-Drone-250 VR仿真 使用说明
============================================


系统架构一览
--------------------------------------------

  ┌─────────────────────────────────────────────────────────────────┐
  │                        Quest 3 头显                             │
  │                                                                 │
  │  ┌──────────────────┐    ┌──────────────────────────────────┐  │
  │  │  Quest2ROS App    │    │  浏览器 (WebXR)                   │  │
  │  │  VR手柄 → 无人机控制 │    │  手势识别 + FPV图传             │  │
  │  │  端口 10000        │    │  localtunnel → 端口 8012         │  │
  │  └────────┬─────────┘    └──────────────┬───────────────────┘  │
  └───────────┼──────────────────────────────┼──────────────────────┘
              │                              │
       SSH隧道 │                              │ HTTPS (localtunnel)
              │                              │
  ┌───────────▼──────────────────────────────▼──────────────────────┐
  │                     Windows 主机                                 │
  │  ssh -L 10000:... -L 8888:...  (SSH端口转发)                    │
  │  localtunnel 隧道 (8012端口暴露)                                  │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │ SSH
  ┌──────────────────────────────▼──────────────────────────────────┐
  │                   Linux 虚拟机 (192.168.100.128)                 │
  │                                                                 │
  │  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
  │  │ quest2ros        │  │ TeleVision        │  │ uav_simulator │  │
  │  │ 端口10000(控制)   │  │ 端口8012(手势+图传)│  │ Gazebo/Rviz   │  │
  │  │ 端口8888(仪表盘)  │  │ stream_camera.py  │  │               │  │
  │  └─────────────────┘  └──────────────────┘  └───────────────┘  │
  └─────────────────────────────────────────────────────────────────┘


============================================
第一部分：VR手柄控制模式 (quest2ros)
============================================

每次启动流程（必须按顺序）
--------------------------------------------

[1] Linux虚拟机 - 启动仿真
    cd /home/dh/桌面/bishe/Fast-Drone-250-master
    ./start_vr_sim.sh
    等待 Rviz 窗口弹出，看到场景中有红色障碍物和DONGHAO雕像

[2] Windows主机 - 建立SSH隧道（双端口：10000控制 + 8888仪表盘）
    打开 PowerShell，执行：
    ssh -N -L 0.0.0.0:10000:127.0.0.1:10000 -L 0.0.0.0:8888:127.0.0.1:8888 dh@192.168.100.128
    输入虚拟机密码，窗口保持打开不要关闭

[3] Quest头显 - 连接控制 + 飞行仪表盘
    - 确保Quest和Windows连接同一个WiFi
    - 打开Quest2ROS App -> IP填Windows的WiFi地址，端口 10000
    - Quest浏览器打开 http://Windows-WiFi-IP:8888  查看飞行数据


VR手柄操作
--------------------------------------------

    右手手柄：
      食指扳机    扣动 -> 无人机飞向你手指指的位置
      A 键        发送目标点

    左手手柄：
      X 键        无人机复位到起飞点 (-15, 0, 1.0)


键盘控制（可选）
--------------------------------------------

    新开虚拟机终端，执行：
    sg docker -c 'docker exec -it fast-drone-250 bash -c \
      "source /opt/ros/noetic/setup.bash && \
       source /workspace/devel/setup.bash && \
       rosrun quest2ros keyboard_control.py"'

    按键功能：
      H = 无人机复位到起点
      Q = 退出键盘控制


============================================
第二部分：手势识别 + FPV图传模式 (TeleVision)
============================================

功能说明
--------------------------------------------

TeleVision 模块提供两个核心功能：

  [手势识别]
    Quest 3 浏览器通过 WebXR API 实时追踪手部25个关键点
    → 通过 WebSocket 发送到 Linux 服务器
    → Preprocessor 坐标变换 (y-up → z-up)
    → 映射为无人机控制指令 (替代VR手柄)

  [FPV 图传]
    摄像头画面（或仿真画面）写入共享内存 (SharedMemory)
    → vuer 服务器编码为 JPEG
    → 通过 WebSocket 推送到 Quest 3 浏览器
    → 左右眼各渲染一层 ImageBackground，产生沉浸式立体视觉

启动流程
--------------------------------------------

[1] Linux虚拟机 - 启动无人机仿真（同第一部分）
    cd /home/dh/桌面/bishe/Fast-Drone-250-master
    ./start_vr_sim.sh

[2] Linux虚拟机 - 启动 TeleVision 服务 (新终端)
    cd /home/dh/桌面/bishe/Fast-Drone-250-master/src/TeleVision/teleop
    conda activate tv310
    python stream_camera.py

    输出 "摄像头已就绪" 或 "使用棋盘格测试画面" 表示成功

[3] Linux虚拟机 - 启动 localtunnel 隧道 (新终端)
    npx localtunnel --port 8012

    输出如 https://xxxx.loca.lt，记住这个地址

[4] Quest 3 - 连接
    - 浏览器打开 localtunnel 输出的 HTTPS 地址
    - 首次访问输入虚拟机 IP (192.168.100.128) 验证
    - 页面加载后点击 "Enter VR"
    - 进入 VR 后即可看到摄像头画面 / 棋盘格测试画面
    - 手势数据会自动回传，可在终端看到手部关键点坐标


TeleVision 文件结构
--------------------------------------------

    src/TeleVision/teleop/
    ├── TeleVision.py        # 主类：vuer WebXR 服务 + 共享内存管理
    ├── stream_camera.py     # 摄像头 → VR 推流脚本 (入口)
    ├── Preprocessor.py      # 手势坐标变换 (WebXR y-up → ROS z-up)
    ├── constants_vuer.py    # 变换矩阵常量
    ├── motion_utils.py      # 矩阵平滑更新
    ├── test_server.py       # 基础连通性测试
    └── webrtc/              # WebRTC 视频流 (可选，需 aiortc)


关键数据流
--------------------------------------------

    VR → 服务器 (WebSocket):
      手部关键点 25点×2手×3坐标  @60Hz
      头部姿态 4×4矩阵           @60Hz
      相机纵横比                  @60Hz

    服务器 → VR (共享内存 → WebSocket → JPEG):
      立体画面 左眼+右眼拼接     ~30fps
      (720×1280 每眼，水平拼接为 720×2560)


============================================
环境安装 (首次使用需执行)
============================================

TeleVision 环境 (Python 3.10)
--------------------------------------------

    conda create -n tv310 python=3.10 -y
    conda activate tv310
    pip install vuer==0.0.32rc7
    pip install numpy opencv-python aiohttp aiohttp_cors pytransform3d PyYAML
    pip install params-proto==2.12.1

localtunnel
--------------------------------------------

    # 无需安装，首次运行时选 y 即可
    npx localtunnel --port 8012


============================================
停止仿真
============================================

    cd /home/dh/桌面/bishe/Fast-Drone-250-master
    ./stop_sim.sh

    TeleVision 和 localtunnel 终端按 Ctrl+C 停止
    如果开了 Windows SSH 隧道也按 Ctrl+C 断开


============================================
常见问题
============================================

Q: Quest显示"未连接" (VR手柄模式)
   1. Linux端仿真已启动（./start_vr_sim.sh），Rviz窗口已弹出
   2. Windows端SSH隧道窗口开着，netstat -ano | findstr :10000 能看到 LISTENING
   3. Quest和Windows连的同一个WiFi
   4. Quest填的IP是Windows的WiFi地址，不是 192.168.100.128

Q: 仪表盘页面打不开
   确认 SSH 隧道包含了 8888 端口（-L 0.0.0.0:8888:127.0.0.1:8888）

Q: TeleVision 页面 503 / 打不开
   1. stream_camera.py 是否已启动（终端显示"服务器已启动"）
   2. localtunnel 终端是否正常运行
   3. 每次重启 localtunnel URL 会变，Quest 要重新输入新地址

Q: Quest 浏览器进入 VR 后黑屏
   1. 检查 stream_camera.py 终端是否有报错
   2. 摄像头不可用时会自动显示棋盘格，黑屏说明图像没传到
   3. 尝试刷新页面重新 Enter VR

Q: 摄像头无法读取画面
   虚拟机 USB 直通不支持 UVC 摄像头 isochronous 传输模式
   → 在宿主机（Windows/Mac）上跑 stream_camera.py
   → 或在虚拟机中摄像头不可用时自动降级为棋盘格测试画面

Q: 无人机飞太高/太低
   高度被限制在 0.5m ~ 3.0m 之间，属于自动保护

Q: Rviz黑屏
   Docker容器内X11授权可能过期，重新执行 start_vr_sim.sh

Q: SSH连不上
   检查虚拟机IP是否正确: hostname -I
   检查SSH服务: systemctl status ssh
