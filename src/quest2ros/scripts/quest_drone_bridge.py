#!/usr/bin/env python3
"""Bridge node: Quest 2/3 VR controller -> Fast-Drone-250 goal commands.

Right controller:
  - Position maps to drone target in simulation world frame
  - Index trigger (>0.5): send goal to drone
  - Button A (upper): send goal to drone

Left controller:
  - Button X (upper): reset drone to home position (-15, 0, 1.0)

Coordinate mapping (Unity VR -> ROS world):
  Unity X(right) -> ROS X
  Unity Y(up)    -> ROS Z
  Unity Z(fwd)   -> -ROS Y
"""

import rospy
from geometry_msgs.msg import PoseStamped
from quest2ros.msg import OVR2ROSInputs

# 无人机起点（复位目标）
HOME_X = -15.0
HOME_Y = 0.0
HOME_Z = 1.0


class QuestDroneBridge:
    def __init__(self):
        self.right_pose = None
        self.goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1)

        rospy.Subscriber("/q2r_right_hand_pose", PoseStamped, self.right_pose_cb)
        rospy.Subscriber("/q2r_right_hand_inputs", OVR2ROSInputs, self.right_inputs_cb)
        rospy.Subscriber("/q2r_left_hand_inputs", OVR2ROSInputs, self.left_inputs_cb)

        # scale factor: VR meters -> sim meters
        self.scale = rospy.get_param("~scale", 30.0)
        # offset in sim world
        self.offset_x = rospy.get_param("~offset_x", 0.0)
        self.offset_y = rospy.get_param("~offset_y", 0.0)
        self.offset_z = rospy.get_param("~offset_z", 0.5)

        self.last_trigger = 0.0
        self.last_left_upper = False  # 左手按键上升沿检测
        self.goal_seq = 0

        rospy.loginfo("[VR Bridge] Ready. Right trigger=goal | Left X=home")

    def vr_to_world(self, vr_x, vr_y, vr_z):
        """Unity VR coords -> simulation world coords."""
        wx =  vr_x * self.scale + self.offset_x
        wy = -vr_z * self.scale + self.offset_y
        # VR Y (up) can be negative (hand below headset), remap to 0.5~3.0m flight height
        wz =  max(0.5, min(3.0, vr_y * self.scale + 2.0))
        return wx, wy, wz

    def right_pose_cb(self, msg):
        self.right_pose = msg

    def right_inputs_cb(self, msg):
        trigger = msg.press_index

        # 右手扳机上升沿 -> 发送飞行目标点
        if trigger > 0.5 and self.last_trigger <= 0.5 and self.right_pose is not None:
            self.send_goal()
        self.last_trigger = trigger

    def left_inputs_cb(self, msg):
        # 左手 X 键 (button_upper) 上升沿 -> 复位无人机到起点
        if msg.button_upper and not self.last_left_upper:
            self.send_home_goal()
        self.last_left_upper = msg.button_upper

    def send_home_goal(self):
        """发送复位目标：无人机飞回起点"""
        goal = PoseStamped()
        goal.header.stamp = rospy.Time.now()
        goal.header.frame_id = "world"
        goal.pose.position.x = HOME_X
        goal.pose.position.y = HOME_Y
        goal.pose.position.z = HOME_Z
        goal.pose.orientation.w = 1.0
        self.goal_pub.publish(goal)
        rospy.loginfo("[VR Bridge] HOME -> (%.0f, %.0f, %.1f)", HOME_X, HOME_Y, HOME_Z)

    def send_goal(self):
        p = self.right_pose.pose.position
        wx, wy, wz = self.vr_to_world(p.x, p.y, p.z)

        goal = PoseStamped()
        goal.header.stamp = rospy.Time.now()
        goal.header.frame_id = "world"
        goal.header.seq = self.goal_seq
        goal.pose.position.x = wx
        goal.pose.position.y = wy
        goal.pose.position.z = wz
        goal.pose.orientation.w = 1.0

        self.goal_pub.publish(goal)
        self.goal_seq += 1
        rospy.loginfo("[VR Bridge] Goal sent: (%.1f, %.1f, %.1f)" % (wx, wy, wz))


def main():
    rospy.init_node("quest_drone_bridge")
    QuestDroneBridge()
    rospy.spin()


if __name__ == "__main__":
    main()
