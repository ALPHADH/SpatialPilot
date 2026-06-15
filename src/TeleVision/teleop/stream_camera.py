"""
Stream camera to Quest 3 via OpenTeleVision.
- Camera works: live video, duplicated to both eyes
- Camera gives only a few frames: show last captured still frames
- Camera completely dead: checkerboard
"""
import cv2
import numpy as np
import time
from multiprocessing import shared_memory, Queue, Event
from TeleVision import OpenTeleVision

CAMERA_ID = 0
WIDTH = 1280
HEIGHT = 720

img_shape = (HEIGHT, 2 * WIDTH, 3)
shm = shared_memory.SharedMemory(create=True, size=np.prod(img_shape) * np.uint8().itemsize)
img_array = np.ndarray((img_shape[0], img_shape[1], 3), dtype=np.uint8, buffer=shm.buf)

tv = OpenTeleVision(
    (HEIGHT, WIDTH),
    shm.name,
    Queue(),
    Event(),
    stream_mode="image",
    ngrok=True,
)

# ---- 摄像头检测 & 预取 -----------------------------------------------------
cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
saved_frames = []          # 存几帧真实画面
camera_ok = False

if cap.isOpened():
    print("正在探测摄像头...")
    for i in range(10):
        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            saved_frames.append(frame)
            camera_ok = True
            print(f"  抓到第 {i+1} 帧 ({frame.shape[1]}x{frame.shape[0]})")
        else:
            time.sleep(0.05)

if camera_ok:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    print(f"摄像头就绪，预取 {len(saved_frames)} 帧")
else:
    print("摄像头无画面 (VM USB 限制)，降级为棋盘格")

print("服务器已启动，等待 Quest 3 连接...")
print("按 Ctrl+C 退出")

# ---- 棋盘格 --------------------------------------------------------------
def make_checkerboard(h, w, count):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    sq = 80
    for i in range(0, h, sq):
        for j in range(0, w, sq):
            c = 200 if (i // sq + j // sq) % 2 == 0 else 100
            img[i:i + sq, j:j + sq] = c
    cv2.putText(img, f"NO CAM | Frame: {count}", (w // 2 - 180, h // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    return img

# ---- 主循环 -------------------------------------------------------------
frame_count = 0
still_idx = 0
last_still_switch = 0

try:
    while True:
        if camera_ok:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                # 更新缓存 (保留最近 5 帧)
                saved_frames = (saved_frames + [frame])[-5:]
            else:
                # 实时流断了，用保存的帧循环播放
                now = time.time()
                if now - last_still_switch > 1.0 and saved_frames:
                    still_idx = (still_idx + 1) % len(saved_frames)
                    last_still_switch = now
                frame = saved_frames[still_idx] if saved_frames else \
                        make_checkerboard(HEIGHT, WIDTH, frame_count)
        else:
            # 完全无摄像头
            frame = make_checkerboard(HEIGHT, WIDTH, frame_count)

        stereo = np.hstack([frame, frame])
        cv2.putText(stereo, "LEFT", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(stereo, "RIGHT", (WIDTH + 30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        np.copyto(img_array, cv2.cvtColor(stereo, cv2.COLOR_BGR2RGB))
        frame_count += 1
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n正在关闭...")
    if cap.isOpened():
        cap.release()
    shm.close()
    shm.unlink()
    print("已退出")
