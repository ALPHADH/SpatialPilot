#!/usr/bin/env python3
import rospy
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point

def create_statue():
    rospy.init_node('donghao_statue')
    pub = rospy.Publisher('/donghao_statue', MarkerArray, queue_size=10)
    rate = rospy.Rate(1)

    marray = MarkerArray()

    # Main text "DONGHAO" as large 3D text
    text = Marker()
    text.header.frame_id = "world"
    text.header.stamp = rospy.Time.now()
    text.ns = "donghao_text"
    text.id = 0
    text.type = Marker.TEXT_VIEW_FACING
    text.action = Marker.ADD
    text.pose.position.x = -5.0
    text.pose.position.y = -8.0
    text.pose.position.z = 1.8
    text.pose.orientation.w = 1.0
    text.scale.z = 1.5  # text height
    text.color.r = 1.0
    text.color.g = 0.84
    text.color.b = 0.0
    text.color.a = 1.0
    text.text = "DONGHAO"
    marray.markers.append(text)

    # Pedestal base (wide flat cube)
    base = Marker()
    base.header.frame_id = "world"
    base.header.stamp = rospy.Time.now()
    base.ns = "donghao_pedestal"
    base.id = 1
    base.type = Marker.CUBE
    base.action = Marker.ADD
    base.pose.position.x = -5.0
    base.pose.position.y = -8.0
    base.pose.position.z = 0.15
    base.pose.orientation.w = 1.0
    base.scale.x = 5.0
    base.scale.y = 0.8
    base.scale.z = 0.3
    base.color.r = 0.3
    base.color.g = 0.3
    base.color.b = 0.3
    base.color.a = 1.0
    marray.markers.append(base)

    # Pillars on sides
    for offset_x, offset_y in [(-2.0, 0), (2.0, 0)]:
        pillar = Marker()
        pillar.header.frame_id = "world"
        pillar.header.stamp = rospy.Time.now()
        pillar.ns = "donghao_pillars"
        pillar.id = 10 + len(marray.markers)
        pillar.type = Marker.CYLINDER
        pillar.action = Marker.ADD
        pillar.pose.position.x = -5.0 + offset_x
        pillar.pose.position.y = -8.0
        pillar.pose.position.z = 0.5
        pillar.pose.orientation.w = 1.0
        pillar.scale.x = 0.3
        pillar.scale.y = 0.3
        pillar.scale.z = 1.0
        pillar.color.r = 0.5
        pillar.color.g = 0.5
        pillar.color.b = 0.5
        pillar.color.a = 1.0
        marray.markers.append(pillar)

    # Top decorative bar
    top = Marker()
    top.header.frame_id = "world"
    top.header.stamp = rospy.Time.now()
    top.ns = "donghao_top"
    top.id = 20
    top.type = Marker.CUBE
    top.action = Marker.ADD
    top.pose.position.x = -5.0
    top.pose.position.y = -8.0
    top.pose.position.z = 1.0
    top.pose.orientation.w = 1.0
    top.scale.x = 4.4
    top.scale.y = 0.4
    top.scale.z = 0.08
    top.color.r = 0.6
    top.color.g = 0.6
    top.color.b = 0.6
    top.color.a = 1.0
    marray.markers.append(top)

    while not rospy.is_shutdown():
        for m in marray.markers:
            m.header.stamp = rospy.Time.now()
        pub.publish(marray)
        rate.sleep()

if __name__ == '__main__':
    create_statue()
