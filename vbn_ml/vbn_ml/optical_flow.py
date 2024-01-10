import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vbn_msgs.msg import OpticalFlow
from cv_bridge import CvBridgeError, CvBridge
import cv2
import sys
import numpy as np
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import String

################################################################################
# Extreme left and extreme right
x_init_el = 0
y_init_el = 0
y_end_el = 0

y_init_er = 0
x_end_er = 0
y_end_er = 0

# Left and right
x_end_l = 0
y_end_l = 0
y_init_l = 0
y_end_r = 0

x_init_r = 0
y_init_r = 0


def set_limit(img_width, img_height):
    # Extreme left and extreme right
    global x_init_el
    global y_init_el
    global y_end_el
    x_init_el = 0
    y_init_el = 0
    y_end_el = int(11 * img_height / 12)

    global x_end_er
    global y_end_er
    global y_init_er
    x_end_er = int(img_width)
    y_end_er = int(11 * img_height / 12)
    y_init_er = 0

    # Left and right
    global x_end_l
    global y_end_l
    global y_init_l
    x_end_l = int(4 * img_width / 12)
    y_end_l = int(7 * img_height / 12)
    y_init_l = int(1 * img_height / 12)

    global x_init_r
    global y_init_r
    global y_end_r
    x_init_r = int(8 * img_width / 12)
    y_init_r = int(1 * img_height / 12)
    y_end_r = int(7 * img_height / 12)


################################################################################

def draw_optical_flow_field(gray_image, points_old, points_new, flow, dt):
    color_img = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
    color_red = [0, 255, 0]  # bgr colorspace
    linewidth = 3

    print("Old points ")  # str(len(points_old)))
    print("New points " + str(len(points_new)))

    for i in range(len(points_new)):
        x_init = points_old[i, 0]
        y_init = points_old[i, 1]

        x_end = points_new[i, 0]
        y_end = points_new[i, 1]

        # print('xinit', type(x_init))
        cv2.line(color_img, (int(x_init), int(y_init)), (int(x_end), int(y_end)), color_red, linewidth)

    cv2.namedWindow('Optical Flow', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Optical Flow', 600, 600)
    cv2.imshow('Optical Flow', color_img)
    cv2.waitKey(10)


################################################################################


class OFCalculator(Node):

    def __init__(self, param):
        super().__init__('optical_flow')

        ########## IMPORTANT PARAMETERS: ##########
        self.image_sub_name = "/camera/camera/color/image_raw"  # NOTE: change topic name depending on real or sim
        self.num_ext_features = 250
        self.num_cen_features = 100
        self.min_feat_threshold = 1.0
        ###########################################
        # Initialize Image acquisition
        self.bridge = CvBridge()
        # Verbose
        # param = 1
        self.show = int(param)
        # Previous Image
        self.prev_image = None
        # Previous key points
        self.prev_kps = np.array([], dtype='f')
        # Previous time instant
        self.prev_time = 0
        # Masks
        self.roi_el = np.array([])
        self.roi_er = np.array([])
        self.roi_c = np.array([])
        # Params for ShiTomasi corner detection
        # self.feature_params = dict(maxCorners=600,
        #						   qualityLevel=0.15,
        #						   minDistance=0,
        #						   blockSize=10)
        # Lucas Kanade Optic Flow parameters
        self.lk_params = dict(winSize=(15, 15),
                              maxLevel=3,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        # ORB Detector/Descriptor initialization
        self.orb_extreme = cv2.ORB_create(self.num_ext_features)
        self.orb_center = cv2.ORB_create(self.num_cen_features)

        # To enable the tracking
        self.tracking = False

        self.min_num_features = (2 * self.num_ext_features + self.num_cen_features) / 2

        # Raw Image Subscriber Jackal PointGrey
        self.image_sub = self.create_subscription(Image, self.image_sub_name, self.callback, 10)

        self.optic_flow_pub = self.create_publisher(OpticalFlow, 'optical_flow', 10)

    def callback(self, data):

        try:
            curr_image = self.bridge.imgmsg_to_cv2(data, "mono8")
        except CvBridgeError as e:
            print(e)
            return
        # print("data",data)
        # Get time stamp
        secs = data.header.stamp.sec
        nsecs = data.header.stamp.nanosec
        curr_time = float(secs) + float(nsecs) * 1e-9
        frequency = 1.0 / (curr_time - self.prev_time)
        print("Frequency: " + str(frequency))

        if self.prev_image is None:
            self.prev_image = curr_image
            self.prev_time = curr_time

            set_limit(data.width, data.height)
            # creating ROI
            self.roi_el = curr_image[y_init_el:y_end_el, x_init_el:x_end_l]
            self.roi_er = curr_image[y_init_er:y_end_er, x_init_r:x_end_er]
            self.roi_c = curr_image[y_init_l:y_end_r, x_end_l:x_init_r]

            keypoints_el = np.array([])
            keypoints_el = np.append(keypoints_el, self.orb_extreme.detect(self.roi_el))
            if (x_init_el != 0) or (y_init_el != 0):
                for i in range(np.size(keypoints_el)):
                    tmp = list(keypoints_el[i].pt)
                    tmp[0] += x_init_el
                    tmp[1] += y_init_el
                    keypoints_el[i].pt = tuple(tmp)

            keypoints_er = np.array([])
            keypoints_er = np.append(keypoints_er, self.orb_extreme.detect(self.roi_er))
            if (x_init_r != 0) or (y_init_er != 0):
                for i in range(np.size(keypoints_er)):
                    tmp = list(keypoints_er[i].pt)
                    tmp[0] += x_init_r
                    tmp[1] += y_init_er
                    keypoints_er[i].pt = tuple(tmp)

            keypoints_c = np.array([])
            keypoints_c = np.append(keypoints_c, self.orb_center.detect(self.roi_c))
            if (x_end_l != 0) or (y_init_l != 0):
                for i in range(np.size(keypoints_c)):
                    tmp = list(keypoints_c[i].pt)
                    tmp[0] += x_end_l
                    tmp[1] += y_init_l
                    keypoints_c[i].pt = tuple(tmp)

            keypoints = np.array([])
            keypoints = np.append(keypoints, keypoints_el)
            keypoints = np.append(keypoints, keypoints_er)
            keypoints = np.append(keypoints, keypoints_c)

            if np.size(keypoints) > 0:
                p0 = cv2.KeyPoint_convert(keypoints)
                self.prev_kps = np.float32(p0.reshape(-1, 1, 2))
                self.tracking = True
            else:
                self.prev_kps = np.array([], dtype='f')
                print("Features detected: 0")
            return

        if self.tracking is False:
            print("new keyframe!")
            # creating ROI
            self.roi_el = curr_image[y_init_el:y_end_el, x_init_el:x_end_l]
            self.roi_er = curr_image[y_init_er:y_end_er, x_init_r:x_end_er]
            self.roi_c = curr_image[y_init_l:y_end_r, x_end_l:x_init_r]

            keypoints_el = np.array([])
            keypoints_el = np.append(keypoints_el, self.orb_extreme.detect(self.roi_el))
            if (x_init_el != 0) or (y_init_el != 0):
                for i in range(np.size(keypoints_el)):
                    tmp = list(keypoints_el[i].pt)
                    tmp[0] += x_init_el
                    tmp[1] += y_init_el
                    keypoints_el[i].pt = tuple(tmp)

            keypoints_er = np.array([])
            keypoints_er = np.append(keypoints_er, self.orb_extreme.detect(self.roi_er))
            if (x_init_r != 0) or (y_init_er != 0):
                for i in range(np.size(keypoints_er)):
                    tmp = list(keypoints_er[i].pt)
                    tmp[0] += x_init_r
                    tmp[1] += y_init_er
                    keypoints_er[i].pt = tuple(tmp)

            keypoints_c = np.array([])
            keypoints_c = np.append(keypoints_c, self.orb_center.detect(self.roi_c))
            if (x_end_l != 0) or (y_init_l != 0):
                for i in range(np.size(keypoints_c)):
                    tmp = list(keypoints_c[i].pt)
                    tmp[0] += x_end_l
                    tmp[1] += y_init_l
                    keypoints_c[i].pt = tuple(tmp)

            keypoints = np.array([])
            keypoints = np.append(keypoints, keypoints_el)
            keypoints = np.append(keypoints, keypoints_er)
            keypoints = np.append(keypoints, keypoints_c)

            if np.size(keypoints) > 0:
                p0 = cv2.KeyPoint_convert(keypoints)
                self.prev_kps = np.float32(p0.reshape(-1, 1, 2))
                self.tracking = True
            else:
                self.prev_kps = np.array([], dtype='f')
                print("Features detected: 0")

        tracked_features, status, error = cv2.calcOpticalFlowPyrLK(self.prev_image, curr_image,
                                                                   self.prev_kps, None,
                                                                   **self.lk_params)

        # Select good points
        good_kps_new = tracked_features[status == 1]
        good_kps_old = self.prev_kps[status == 1]
        # print("len matches "+ str(len(good_kps_new)))

        if np.size(good_kps_new) < self.min_feat_threshold * np.size(self.prev_kps):
            self.tracking = False
            self.prev_kps = np.array([], dtype='f')
        elif np.size(good_kps_new) <= self.min_num_features:
            self.tracking = False
            self.prev_kps = np.array([], dtype='f')
        else:
            self.prev_kps = np.float32(good_kps_new.reshape(-1, 1, 2))

        # Get time between images
        dt = curr_time - self.prev_time

        # Calculate flow field
        flow = good_kps_new - good_kps_old
        print("Flow: ", type(good_kps_old))
        # Draw the flow field

        if self.show == 1:
            draw_optical_flow_field(curr_image, good_kps_old, good_kps_new, flow, dt)
            # Publish Optical Flow data to rostopic
        msg = OpticalFlow()
        msg.header.stamp.sec = secs
        msg.header.stamp.nanosec = nsecs

        msg.height = data.height
        msg.width = data.width

        msg.dt = dt * 1.0 # in msec

        msg.x = Float32MultiArray(data = good_kps_old[:, 0])
        msg.y = Float32MultiArray(data = good_kps_old[:, 1])
        msg.vx = Float32MultiArray(data = flow[:, 0] / dt)
        msg.vy = Float32MultiArray(data = flow[:, 1] / dt)
        self.optic_flow_pub.publish(msg)

        self.prev_image = curr_image
        self.prev_time = curr_time


def main(args=None):
    if len(sys.argv) < 2:
        parameter = str(0)
    else:
        parameter = 1

    rclpy.init(args=args)

    optical_flow = OFCalculator(parameter)

    rclpy.spin(optical_flow)

    optical_flow.destroy_node()
    rclpy.shutdown()



