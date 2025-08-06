import cv2
import mediapipe as mp
import math

# Mediapipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Button class
class Button:
    def __init__(self, pos, width, height, text):
        self.pos = pos
        self.width = width
        self.height = height
        self.text = text

    def draw(self, img):
        x, y = self.pos
        cv2.rectangle(img, self.pos, (x + self.width, y + self.height), (50, 50, 50), cv2.FILLED)
        cv2.rectangle(img, self.pos, (x + self.width, y + self.height), (255, 255, 255), 2)
        font_scale = 2
        text_size, _ = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_PLAIN, font_scale, 2)
        text_x = x + (self.width - text_size[0]) // 2
        text_y = y + (self.height + text_size[1]) // 2
        cv2.putText(img, self.text, (text_x, text_y), cv2.FONT_HERSHEY_PLAIN, font_scale, (255, 255, 255), 2)

    def is_clicked(self, x, y):
        bx, by = self.pos
        return bx < x < bx + self.width and by < y < by + self.height

# Calculator buttons (4x4 grid)
labels = [
    ["7", "8", "9", "+"],
    ["4", "5", "6", "-"],
    ["1", "2", "3", "*"],
    ["C", "0", "=", "/"]
]

# Button size and spacing
button_w, button_h = 100, 100
spacing = 20
grid_cols = 4
grid_rows = 4

# Video capture
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Compute centered positions
frame_w = int(cap.get(3))
frame_h = int(cap.get(4))
grid_width = grid_cols * button_w + (grid_cols - 1) * spacing
grid_height = grid_rows * button_h + (grid_rows - 1) * spacing
start_x = (frame_w - grid_width) // 2
start_y = (frame_h - grid_height) // 2

# Create buttons
button_list = []
for i in range(grid_rows):
    for j in range(grid_cols):
        xpos = start_x + j * (button_w + spacing)
        ypos = start_y + i * (button_h + spacing)
        button_list.append(Button((xpos, ypos), button_w, button_h, labels[i][j]))

# Calculator state
expression = ""
last_click_frame = 0
delay_between_clicks = 20  # frames
frame_counter = 0

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    frame_counter += 1

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    h_img, w_img, _ = img.shape

    # Draw all buttons
    for button in button_list:
        button.draw(img)

    # Draw expression box
    cv2.rectangle(
        img,
        (start_x, start_y - 70),
        (start_x + grid_width, start_y - 20),
        (50, 50, 50),
        cv2.FILLED
    )
    cv2.putText(
        img,
        expression,
        (start_x + 10, start_y - 35),
        cv2.FONT_HERSHEY_PLAIN,
        2,
        (255, 255, 255),
        2
    )

    # Process hand landmarks
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lm = handLms.landmark

            # Get index finger tip and thumb tip
            index_finger = lm[8]
            thumb_finger = lm[4]

            x1, y1 = int(index_finger.x * w_img), int(index_finger.y * h_img)
            x2, y2 = int(thumb_finger.x * w_img), int(thumb_finger.y * h_img)

            # Draw markers
            cv2.circle(img, (x1, y1), 8, (0, 255, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (0, 255, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)

            # Measure pinch distance
            distance = math.hypot(x2 - x1, y2 - y1)

            if distance < 40 and frame_counter - last_click_frame > delay_between_clicks:
                last_click_frame = frame_counter
                cursor_x, cursor_y = x1, y1

                for button in button_list:
                    if button.is_clicked(cursor_x, cursor_y):
                        val = button.text
                        if val == "=":
                            try:
                                expression = str(eval(expression))
                            except:
                                expression = "Error"
                        elif val == "C":
                            expression = ""
                        else:
                            expression += val

    cv2.imshow("Hand Calculator", img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
