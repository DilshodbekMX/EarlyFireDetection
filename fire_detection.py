import cv2

from yolov8 import YOLOv8

# Initialize the webcam
cap = cv2.VideoCapture("rtsp://admin:Admin777.@192.168.1.64:554/Streaming/Channels/1")
img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)/2)
img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)/2)
dim = (img_width, img_height)
# Initialize YOLOv7 object detector
model_path = "fire.onnx"
yolov8_detector = YOLOv8(model_path, conf_thres=0.5, iou_thres=0.5)

while cap.isOpened():

    # Read frame from the video
    ret, frame = cap.read()
    frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    if not ret:
        break

    # Update object localizer
    boxes, scores, class_ids = yolov8_detector(frame)

    combined_img = yolov8_detector.draw_detections(frame)
    cv2.imshow("Detected Objects", combined_img)

    # Press key q to stop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
