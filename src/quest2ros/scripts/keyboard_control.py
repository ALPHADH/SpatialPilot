#!/usr/bin/env python3
"""
键盘控制节点：在仿真中通过按键控制无人机。

按键功能：
  H / h  --  复位无人机到起点 (-15, 0, 1.0)
  Q / q  --  退出本节点

启动方式（在单独终端中）：
  sg docker -c 'docker exec -it fast-drone-250 bash -c \
    "source /opt/ros/noetic/setup.bash && source /workspace/devel/setup.bash && \
     rosrun quest2ros keyboard_control.py"'
"""

import rospy
import sys
import select
import termios
import tty
from geometry_msgs.msg import PoseStamped

# 无人机起点（与 single_run_in_sim.launch 中 init_x/init_y/init_z 一致）
HOME_X = -15.0
HOME_Y = 0.0
HOME_Z = 1.0


def get_key(settings):
    """非阻塞读取单个按键，返回字符或 None"""
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = None
    if rlist:
        key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def send_home_goal(pub):
    """发送复位目标点：让无人机飞回起点"""
    goal = PoseStamped()
    goal.header.stamp = rospy.Time.now()
    goal.header.frame_id = "world"
    goal.pose.position.x = HOME_X
    goal.pose.position.y = HOME_Y
    goal.pose.position.z = HOME_Z
    goal.pose.orientation.w = 1.0
    pub.publish(goal)
    rospy.loginfo("[键盘控制] 无人机复位 -> (%.0f, %.0f, %.1f)", HOME_X, HOME_Y, HOME_Z)


def main():
    rospy.init_node("keyboard_control")
    goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1)

    # 保存终端设置以便恢复
    old_settings = termios.tcgetattr(sys.stdin)

    rospy.loginfo("[键盘控制] 已启动 | H=复位起点 | Q=退出")

    try:
        while not rospy.is_shutdown():
            key = get_key(old_settings)
            if key is None:
                continue

            if key.lower() == 'h':
                send_home_goal(goal_pub)
            elif key.lower() == 'q':
                rospy.loginfo("[键盘控制] 退出")
                break

    except Exception as e:
        rospy.logerr("[键盘控制] 错误: %s", e)
    finally:
        # 恢复终端原始设置，避免终端乱码
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        rospy.loginfo("[键盘控制] 终端已恢复")


if __name__ == "__main__":
    main()
