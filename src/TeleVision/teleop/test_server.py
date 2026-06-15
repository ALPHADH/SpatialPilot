"""
Minimal test server for Open-TeleVision with Quest 3.
Streams a test pattern (checkerboard) to verify WebXR connectivity.
"""
import numpy as np
import time
import cv2
from multiprocessing import shared_memory, Queue, Event
from TeleVision import OpenTeleVision

# Configuration
RESOLUTION = (720, 1280)
CROP_SIZE_W = 0
CROP_SIZE_H = 0
RES_CROPPED = (RESOLUTION[0] - CROP_SIZE_H, RESOLUTION[1] - 2 * CROP_SIZE_W)

IMG_SHAPE = (RES_CROPPED[0], 2 * RES_CROPPED[1], 3)  # 720 x 2560
IMG_HEIGHT, IMG_WIDTH = RES_CROPPED[:2]  # 720 x 1280

# Create shared memory for stereo image
shm = shared_memory.SharedMemory(create=True, size=np.prod(IMG_SHAPE) * np.uint8().itemsize)
shm_name = shm.name
img_array = np.ndarray((IMG_SHAPE[0], IMG_SHAPE[1], 3), dtype=np.uint8, buffer=shm.buf)

# Queues for WebRTC (not used in image mode)
image_queue = Queue()
toggle_streaming = Event()

# Start OpenTeleVision with ngrok mode for Quest 3
print("Starting OpenTeleVision server...")
print(f"Shared memory: {shm_name}")
print(f"Image shape: {IMG_SHAPE}")
print()

tv = OpenTeleVision(
    RES_CROPPED,
    shm_name,
    image_queue,
    toggle_streaming,
    stream_mode="image",
    ngrok=True  # Required for Quest 3
)

print("Server started! Awaiting connection from Quest 3...")
print()

# Test pattern
def generate_test_pattern(h, w):
    """Generate a checkerboard test pattern."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    # Checkerboard
    square_size = 80
    for i in range(0, h, square_size):
        for j in range(0, w, square_size):
            color = 255 if (i // square_size + j // square_size) % 2 == 0 else 128
            img[i:i+square_size, j:j+square_size] = color
    return img

# Generate test patterns for left and right eyes
left_pattern = generate_test_pattern(IMG_HEIGHT, IMG_WIDTH)
right_pattern = generate_test_pattern(IMG_HEIGHT, IMG_WIDTH)

# Add text to distinguish left/right
cv2.putText(left_pattern, "LEFT EYE", (IMG_WIDTH//2 - 100, IMG_HEIGHT//2),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
cv2.putText(right_pattern, "RIGHT EYE", (IMG_WIDTH//2 - 100, IMG_HEIGHT//2),
            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

print("Entering main loop. Press Ctrl+C to exit.")
print("Open the ngrok HTTPS URL on your Quest 3 browser and click 'Enter VR'")
print()
print("=" * 60)

try:
    frame_count = 0
    while True:
        start = time.time()

        # Read VR tracking data (non-blocking)
        try:
            left_hand = tv.left_hand
            right_hand = tv.right_hand
            head_mat = tv.head_matrix
            if np.any(head_mat):
                print(f"\r[Frame {frame_count}] "
                      f"Head pos: ({head_mat[0,3]:.2f}, {head_mat[1,3]:.2f}, {head_mat[2,3]:.2f}) | "
                      f"Left hand: {'tracked' if np.any(left_hand) else 'not tracked'} | "
                      f"Right hand: {'tracked' if np.any(right_hand) else 'not tracked'}   ",
                      end="", flush=True)
        except Exception:
            pass

        # Write the stereo image (left | right) to shared memory
        stereo_img = np.hstack([left_pattern, right_pattern])
        np.copyto(img_array, stereo_img)

        frame_count += 1
        elapsed = time.time() - start
        sleep_time = max(0, 1/30 - elapsed)
        time.sleep(sleep_time)

except KeyboardInterrupt:
    print("\n\nShutting down...")
    shm.close()
    shm.unlink()
    print("Done.")
