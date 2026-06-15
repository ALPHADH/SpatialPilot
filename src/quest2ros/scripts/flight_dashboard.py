#!/usr/bin/env python3
"""
飞行数据仪表盘：提供HTTP网页，在Quest浏览器中实时查看无人机飞行数据。

访问方式：Quest浏览器打开 http://<Windows-WiFi-IP>:8888
"""

import rospy
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker


# 最新飞行数据缓存
flight_data = {
    "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0,
    "goal_x": 0.0, "goal_y": 0.0, "goal_z": 0.0,
    "dist_to_goal": 0.0,
    "state": "WAIT_TARGET",
    "fps": 0,
}
_lock = threading.Lock()
_frame_count = 0
_last_fps_time = None


def pose_cb(msg):
    global _frame_count, _last_fps_time
    if _last_fps_time is None:
        _last_fps_time = rospy.Time.now()
    with _lock:
        flight_data["pos_x"] = msg.pose.position.x
        flight_data["pos_y"] = msg.pose.position.y
        flight_data["pos_z"] = msg.pose.position.z
        # 计算距离
        dx = flight_data["pos_x"] - flight_data["goal_x"]
        dy = flight_data["pos_y"] - flight_data["goal_y"]
        dz = flight_data["pos_z"] - flight_data["goal_z"]
        flight_data["dist_to_goal"] = (dx*dx + dy*dy + dz*dz) ** 0.5

        # FPS
        _frame_count += 1
        now = rospy.Time.now()
        dt = (now - _last_fps_time).to_sec()
        if dt >= 1.0:
            flight_data["fps"] = round(_frame_count / dt, 1)
            _frame_count = 0
            _last_fps_time = now


def goal_cb(msg):
    with _lock:
        flight_data["goal_x"] = msg.pose.position.x
        flight_data["goal_y"] = msg.pose.position.y
        flight_data["goal_z"] = msg.pose.position.z


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            self.send_json_data()
        elif self.path == "/":
            self.send_html_page()
        else:
            self.send_response(404)
            self.end_headers()

    def send_json_data(self):
        with _lock:
            data = dict(flight_data)
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html_page(self):
        html = HTML_PAGE.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        pass  # 抑制HTTP请求日志


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fast-Drone-250 HUD</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: #0a0a1a;
    color: #00ff88;
    font-family: 'Courier New', monospace;
    padding: 20px;
    min-height: 100vh;
  }
  h1 {
    text-align: center;
    font-size: 3vw;
    letter-spacing: 8px;
    color: #00ccff;
    margin-bottom: 20px;
    text-shadow: 0 0 20px #00ccff;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    max-width: 800px;
    margin: 0 auto;
  }
  .card {
    background: #0d0d2a;
    border: 2px solid #1a3a4a;
    border-radius: 12px;
    padding: 18px;
  }
  .card.full { grid-column: 1 / -1; }
  .label {
    font-size: 1.5vw;
    color: #6688aa;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-bottom: 8px;
  }
  .value {
    font-size: 5vw;
    font-weight: bold;
    color: #00ffaa;
    text-shadow: 0 0 10px rgba(0,255,170,0.5);
  }
  .value.small { font-size: 3vw; }
  .value.warn { color: #ffaa00; text-shadow: 0 0 10px rgba(255,170,0,0.5); }
  .state-badge {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 2.5vw;
    font-weight: bold;
    letter-spacing: 3px;
  }
  .state-WAIT_TARGET { background:#1a3a2a; color:#00ff88; border:2px solid #00ff88; }
  .state-GEN_NEW_TRAJ { background:#1a2a3a; color:#00ccff; border:2px solid #00ccff; }
  .state-EXEC_TRAJ { background:#3a2a1a; color:#ffaa00; border:2px solid #ffaa00; }
  .bar-container {
    background: #0d0d2a;
    border-radius: 10px;
    height: 25px;
    margin-top: 5px;
    overflow: hidden;
    border: 1px solid #1a3a4a;
  }
  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #00ff88, #00ccff);
    border-radius: 10px;
    transition: width 0.2s;
  }
  .coord-row { display:flex; gap:20px; margin-top:5px; }
  .coord-item { flex:1; }
  .coord-label { font-size:1.2vw; color:#6688aa; }
  .coord-value { font-size:2.5vw; color:#00ffaa; }
  .fps { text-align:center; font-size:1.5vw; color:#334455; margin-top:15px; }
</style>
</head>
<body>

<h1>DRONE HUD</h1>

<div class="grid">
  <div class="card full" style="text-align:center">
    <div class="label">STATUS</div>
    <span id="state" class="state-badge state-WAIT_TARGET">WAIT_TARGET</span>
  </div>

  <div class="card">
    <div class="label">Position X</div>
    <div class="value" id="pos_x">0.0</div>
  </div>
  <div class="card">
    <div class="label">Position Y</div>
    <div class="value" id="pos_y">0.0</div>
  </div>
  <div class="card">
    <div class="label">Position Z</div>
    <div class="value small" id="pos_z">0.0</div>
  </div>
  <div class="card">
    <div class="label">To Goal (m)</div>
    <div class="value small warn" id="dist">0.0</div>
  </div>

  <div class="card full">
    <div class="label">Goal Point</div>
    <div class="coord-row">
      <div class="coord-item">
        <div class="coord-label">X</div>
        <div class="coord-value" id="goal_x">--</div>
      </div>
      <div class="coord-item">
        <div class="coord-label">Y</div>
        <div class="coord-value" id="goal_y">--</div>
      </div>
      <div class="coord-item">
        <div class="coord-label">Z</div>
        <div class="coord-value" id="goal_z">--</div>
      </div>
    </div>
  </div>
</div>

<div class="fps" id="fps">FPS: --</div>

<script>
const POLL_MS = 150;

function fmt(n, d) { return Number(n).toFixed(d); }

async function poll() {
  try {
    let r = await fetch('/data');
    let d = await r.json();

    document.getElementById('pos_x').textContent = fmt(d.pos_x, 1);
    document.getElementById('pos_y').textContent = fmt(d.pos_y, 1);
    document.getElementById('pos_z').textContent = fmt(d.pos_z, 1);
    document.getElementById('dist').textContent = fmt(d.dist_to_goal, 1);
    document.getElementById('goal_x').textContent = fmt(d.goal_x, 1);
    document.getElementById('goal_y').textContent = fmt(d.goal_y, 1);
    document.getElementById('goal_z').textContent = fmt(d.goal_z, 1);
    document.getElementById('fps').textContent = 'FPS: ' + d.fps;

    let st = document.getElementById('state');
    st.textContent = d.state;
    st.className = 'state-badge state-' + d.state;
  } catch(e) {}
  setTimeout(poll, POLL_MS);
}

poll();
</script>

</body>
</html>"""


def main():
    rospy.init_node("flight_dashboard")

    rospy.Subscriber("/drone_0_odom_visualization/pose", PoseStamped, pose_cb)
    rospy.Subscriber("/drone_0_ego_planner_node/goal_point", Marker, goal_cb)

    port = rospy.get_param("~port", 8888)
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    rospy.loginfo("[Dashboard] http://0.0.0.0:%d", port)

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    rospy.spin()


if __name__ == "__main__":
    main()
