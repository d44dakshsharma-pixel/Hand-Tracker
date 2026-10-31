import cv2
import numpy
import math
import pyautogui
import os
import mediapipe as mp

class S_click:
    def __init__(self):
        self.armed = True
        self.frames = 0
        self.hold_threshold = 10

    def update(self, active):
        if active:
            if self.armed:
                self.frames += 1
                
                if self.frames > self.hold_threshold:
                    pyautogui.click()
                    self.armed = False
        else:
            self.armed = True
            self.frames = 0

class D_click:
    def __init__(self):
        self.armed = True
        self.frames = 0
        self.hold_threshold = 10

    def update(self, active):
        if active:
            if self.armed:
                self.frames += 1

                if self.frames > self.hold_threshold:
                    pyautogui.doubleClick()
                    self.armed = False
        else:
            self.armed = True
            self.frames = 0

pi = math.pi

screen_w, screen_h = pyautogui.size()

prev_hand_x = prev_hand_y = prev_cur_x = prev_cur_y = 0.0
sensitivity = 0.6
dead_zone = 5
was_moving = False

mouse_down = False
mouse_up = True
was_dragging = False

vol_control_enabled = True

mute_frames = 0
mute_armed = True

play_pause_armed = True
play_pause_frames = 0

translation_armed = True
translation_frames = 0
is_translating = False
accumulated_translation = 0.0

was_scrolling = False
accumulated_scroll = 0
scroll_sensitivity = 5

allow_sequence_append = True
sequence_frames = 0
sequence_frames_threshold = 15
initialize_sequence = False
sequence = []

run = True

pyautogui.PAUSE = 0.00001

# left_hand = {
#     "curr_index_tip_x" : 0.0,
#     "curr_index_tip_y" : 0.0,
#     "prev_index_tip_x" : 0.0,
#     "prev_index_tip_y" : 0.0,
#     "prev_wrist_x" : 0.0,
#     "new_wrist_x" : 0.0,
#     "prev_thumb_tip_y" : 0.0,
#     "new_thumb_tip_y" : 0.0
# }

class Left_Hand():
    curr_index_tip_x = 0.0
    curr_index_tip_ = 0.0
    prev_index_tip_x = 0.0
    prev_index_tip_y = 0.0
    prev_wrist_x = 0.0
    new_wrist_x = 0.0
    prev_thumb_tip_y = 0.0
    new_thumb_tip_y = 0.0

left_hand = Left_Hand()

window_center_x = window_center_y = 0.5 
translation_vector = numpy.array([0.5, 0.5])

eps = 1e-6

pyautogui.FAILSAFE = False

def joint_open(lm, a : int, b : int, c : int, thresh = 0.7) -> bool:

    v1 = numpy.array([lm[b].x - lm[a].x, lm[b].y - lm[a].y])
    v2 = numpy.array([lm[c].x - lm[b].x, lm[c].y - lm[b].y])

    v1_mag = numpy.linalg.norm(v1)
    v2_mag = numpy.linalg.norm(v2)

    if v1_mag <= eps or v2_mag < eps:
        return False

    v1_dot_v2 = numpy.dot(v1, v2)

    cos1 = v1_dot_v2/(v1_mag * v2_mag)

    return (cos1 > thresh)

def in_proximity(lm, landmark1 : int, landmark2 : int, width, height, threshold = 25):
    x1, y1 = lm[landmark1].x, lm[landmark1].y
    x2, y2 = lm[landmark2].x, lm[landmark2].y
    dist_x = (x1 - x2) * width 
    dist_y = (y1 - y2) * height 

    if abs(dist_x) < threshold and abs(dist_y) < threshold:
        return True
    return False

def finger_state(lm, finger : str):
    lm0 = 0
    lm1 = lm2 = lm3 = lm4 = None
    finger_state = "closed"

    if finger == "Index":
        lm1, lm2, lm3, lm4 = [5, 6, 7, 8]
    elif finger == "Middle":
        lm1, lm2, lm3, lm4 = [9, 10, 11, 12]
    elif finger == "Ring":
        lm1, lm2, lm3, lm4 = [13, 14, 15, 16]
    elif finger == "Pinky":
        lm1, lm2, lm3, lm4 = [17, 18, 19, 20]

    if joint_open(lm, lm0, lm1, lm2) and joint_open(lm, lm1, lm2, lm3) and joint_open(lm, lm2, lm3, lm4):
        finger_state = "open"

    return finger_state

def thumb_state(lm):
    lm0 = 0
    lm1 = 1
    lm2 = 2
    lm3 = 3
    lm4 = 4
    thumb_state = "closed"

    if joint_open(lm, lm0, lm1, lm2) and joint_open(lm, lm1, lm2, lm3) and joint_open(lm, lm2, lm3, lm4):
        thumb_state = "open"

    return thumb_state

s_click = S_click()
d_click = D_click()

# Initialize MediaPipe Hands solution
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Utility for drawing landmarks
mp_draw = mp.solutions.drawing_utils

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Flip the image for mirror view
    frame = cv2.flip(frame, 1)

    # Convert BGR (OpenCV) to RGB (MediaPipe)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    window_h, window_w = frame.shape[0], frame.shape[1]

    # If hands are detected
    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            lm = hand_landmarks.landmark
            handedness = results.multi_handedness[idx]
            hand_label = handedness.classification[0].label
            
            thumb = thumb_state(lm)
            index = finger_state(lm, "Index")
            middle = finger_state(lm, "Middle")
            ring = finger_state(lm, "Ring")
            pinky = finger_state(lm, "Pinky")

            state = [thumb, index, middle, ring, pinky]

            gesture = "UNKNOWN"

            if hand_label == "Right":

                if state == ["open", "open", "open", "open", "open"]:
                    gesture = "OPEN PALM"
                elif state == ["closed", "closed", "closed", "closed", "closed"]:
                    gesture = "MOVE"
                elif state == ["closed", "open", "closed", "closed", "closed"]:
                    gesture = "S_CLICK"
                elif state == ["closed", "open", "open", "closed", "closed"]:
                    gesture = "D_CLICK"
                elif in_proximity(lm, 4, 8, window_w, window_h, 25) and [middle, ring, pinky] == ["open", "open", "open"]:
                    gesture = "DRAG"

                if in_proximity(lm, 4, 12, window_w, window_h, 35) and [index, ring, pinky] == ["open", "open", "open"]:
                    if allow_sequence_append and sequence_frames < sequence_frames_threshold:
                        sequence.append("middle")
                        allow_sequence_append = False
                        sequence_frames = 0
                elif in_proximity(lm, 4, 16, window_w, window_h, 35) and [index, middle, pinky] == ["open", "open", "open"]:
                    if allow_sequence_append and sequence_frames < sequence_frames_threshold:
                        sequence.append("ring")
                        allow_sequence_append = False
                        sequence_frames = 0
                elif in_proximity(lm, 4, 20, window_w, window_h, 35) and [index,middle, ring] == ["open", "open", "open"]:
                    if allow_sequence_append and sequence_frames < sequence_frames_threshold:
                        sequence.append("pinky")
                        allow_sequence_append = False
                        sequence_frames = 0
                else:
                    allow_sequence_append = True

                if sequence == ["middle", "middle", "ring", "pinky", "middle"]:
                    if run:
                        os.startfile(r"C:\Users\d44da\Music\STARK\Brown Rang.mp3")
                        run = False
                elif sequence == ["ring", "ring", "middle", "middle", "pinky"]:
                    if run:
                        os.startfile(r"C:\Users\d44da\Music\STARK\Gigachad theme ( Phonk house version)   Slowed and Reverb.mp3")
                        run = False
                else:
                    run = True

                if gesture == "MOVE":
                    wrist = lm[0]
                    if not was_moving:
                        prev_cur_x, prev_cur_y = pyautogui.position()
                        prev_hand_x, prev_hand_y = wrist.x, wrist.y
                        was_moving = True

                    curr_hand_x, curr_hand_y = wrist.x, wrist.y

                    hand_dx = curr_hand_x - prev_hand_x
                    hand_dy = curr_hand_y - prev_hand_y

                    new_cur_x = prev_cur_x + (hand_dx * screen_w * sensitivity)
                    new_cur_y = prev_cur_y + (hand_dy * screen_h * sensitivity)

                    move_x = hand_dx * window_w
                    move_y = hand_dy * window_h

                    if int(abs(move_x)) >= dead_zone or int(abs(move_y)) >= dead_zone:
                        pyautogui.moveTo(new_cur_x, new_cur_y)

                    prev_cur_x, prev_cur_y = new_cur_x, new_cur_y
                    prev_hand_x, prev_hand_y = curr_hand_x, curr_hand_y
                else:
                    was_moving = False

                s_click.update(gesture == "S_CLICK")

                d_click.update(gesture == "D_CLICK")
                
                if gesture == "DRAG":
                    thumb_tip = lm[4]
                    if not was_dragging:
                        prev_cur_x, prev_cur_y = pyautogui.position()
                        prev_hand_x, prev_hand_y = thumb_tip.x, thumb_tip.y
                        was_dragging = True

                    curr_hand_x, curr_hand_y = thumb_tip.x, thumb_tip.y

                    hand_dx = (curr_hand_x - prev_hand_x)
                    hand_dy = (curr_hand_y - prev_hand_y)

                    new_cur_x = prev_cur_x + (hand_dx * screen_w * sensitivity)
                    new_cur_y = prev_cur_y + (hand_dy * screen_h * sensitivity)

                    move_x = hand_dx * window_w
                    move_y = hand_dy * window_h

                    if abs(move_x) > dead_zone or abs(move_y) > dead_zone:
                        if not mouse_down:
                            pyautogui.mouseDown()
                            mouse_down = True
                            mouse_up = False
                        pyautogui.moveTo(new_cur_x, new_cur_y)

                    prev_cur_x, prev_cur_y = new_cur_x, new_cur_y
                    prev_hand_x, prev_hand_y = curr_hand_x, curr_hand_y
                else:
                    was_dragging = False
                    if not mouse_up:
                        pyautogui.mouseUp()
                        mouse_down = False
                        mouse_up = True
                
                print(state)

                cv2.putText(frame, f"{gesture} | {hand_label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if hand_label == "Left":
                
                if [index, middle, ring, pinky] == ["open", "closed", "closed", "closed"]:
                    gesture = "VOLUME"
                elif in_proximity(lm, 4, 8, window_w, window_h, 35) and in_proximity(lm, 4, 12, window_w, window_h, 35) and in_proximity(lm, 4, 16, window_w, window_h, 35) and in_proximity(lm, 4, 20, window_w, window_h, 35):
                    gesture = "MUTE"
                elif state == ["open", "open", "open", "open", "open"]:
                    gesture = "TRACK CHANGE"
                elif state == ["open", "open", "open", "closed", "closed"]:
                    gesture = "PLAY_PAUSE"
                elif in_proximity(lm, 4, 8, window_w, window_h, 25) and [middle, ring, pinky] == ["open", "open", "open"]:
                    gesture = "SCROLL"

                if gesture == "VOLUME":
                    index_tip = lm[8]

                    if vol_control_enabled:
                        left_hand.prev_index_tip_x = index_tip.x
                        left_hand.prev_index_tip_y = index_tip.y
                        vol_control_enabled = False

                    left_hand.curr_index_tip_x = index_tip.x
                    left_hand.curr_index_tip_y = index_tip.y

                    v1 = numpy.array([left_hand.curr_index_tip_x, left_hand.curr_index_tip_y]) - translation_vector
                    v0 = numpy.array([left_hand.prev_index_tip_x, left_hand.prev_index_tip_y]) - translation_vector

                    v0_mag = numpy.linalg.norm(v0)
                    v1_mag = numpy.linalg.norm(v1)

                    if v0_mag > eps and v1_mag > eps:
                        alpha_1 = math.atan2(v0[1], v0[0])
                        alpha_2 = math.atan2(v1[1], v1[0])

                        d_alpha = alpha_2 - alpha_1
                        d_alpha_degrees = d_alpha * (180/pi)

                        if d_alpha_degrees > 5:
                            pyautogui.press("volumeup")
                        elif d_alpha_degrees < -5:
                            pyautogui.press("volumedown")
                        
                    left_hand.prev_index_tip_x = left_hand.curr_index_tip_x
                    left_hand.prev_index_tip_y = left_hand.curr_index_tip_y
                else:
                    vol_control_enabled = True

                if gesture == "MUTE":
                    if mute_armed:
                        mute_frames = mute_frames+1
                        
                        if mute_frames > 40:
                            pyautogui.press("volumemute")
                            mute_armed = False
                else:
                    mute_frames = 0
                    mute_armed = True

                if gesture == "TRACK CHANGE":
                    wrist = lm[0]
                    if not is_translating:
                        left_hand.prev_wrist_x = wrist.x
                        is_translating = True
                    if translation_armed:
                        left_hand.new_wrist_x = wrist.x
                        dx = left_hand.new_wrist_x - left_hand.prev_wrist_x
                        accumulated_translation = accumulated_translation + dx
                        translation_frames = translation_frames + 1

                        if translation_frames < 25:
                            if accumulated_translation > 0.5:
                                pyautogui.press("nexttrack")
                                translation_armed = False
                            elif accumulated_translation < -0.5:
                                pyautogui.press("prevtrack")
                                translation_armed = False
                        
                        left_hand.prev_wrist_x = left_hand.new_wrist_x
                else:
                    is_translating = False
                    translation_armed = True
                    accumulated_translation = 0
                    translation_frames = 0

                if gesture == "PLAY_PAUSE":
                    if play_pause_armed:
                        play_pause_frames = play_pause_frames+1

                        if play_pause_frames > 40:
                            pyautogui.press("playpause")
                            play_pause_armed = False
                else:
                    play_pause_armed = True
                    play_pause_frames = 0

                if gesture == "SCROLL":
                    thumb_tip = lm[4]

                    if not was_scrolling:
                        left_hand.prev_thumb_tip_y = wrist.y
                        was_scrolling = True

                    left_hand.new_thumb_tip_y = thumb_tip.y
                    dy = left_hand.new_thumb_tip_y - left_hand.prev_thumb_tip_y
                    accumulated_scroll = accumulated_scroll + dy
                    accumulated_scroll = accumulated_scroll * scroll_sensitivity
                    if accumulated_scroll > 0.25 and abs(dy * window_h) > 5:
                        pyautogui.scroll(100)
                        accumulated_scroll = 0
                    elif accumulated_scroll < -0.25 and abs(dy * window_h) > 5:
                        pyautogui.scroll(-100)
                        accumulated_scroll = 0

                    left_hand.prev_thumb_tip_y = left_hand.new_thumb_tip_y
                else:
                    was_scrolling = False

                cv2.putText(frame, f"{gesture} | {hand_label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            if len(sequence) != 0:
                initialize_sequence = True
            else:
                initialize_sequence = False
            if initialize_sequence:
                sequence_frames += 1
            if sequence_frames > sequence_frames_threshold:
                sequence = []
                sequence_frames = 0
                initialize_sequence = False
            print(sequence_frames)

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Show output
    cv2.imshow("Hand Tracking", frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()