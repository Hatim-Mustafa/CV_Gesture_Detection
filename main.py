import cv2
from capture    import FrameCapture
from classifier import GestureClassifier
from sender     import GestureSender
from state_receiver import StateReceiver

def run():
    cap        = FrameCapture()
    classifier = GestureClassifier()
    sender     = GestureSender()
    state_rx   = StateReceiver()

    print("[gesture] running — press Q to quit")

    while True:
        landmarks, frame = cap.get_landmarks()

        state_rx.update()
        state = state_rx.get()
        print(state)

        if frame is None:
            break

        gesture = classifier.update(landmarks)

        if gesture:
            print(f"[gesture] → {gesture}")
            sender.send(gesture)

        # debug overlay
        if frame is not None:
            label = gesture or "..."
            cv2.putText(frame, label, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 120), 2)
            cv2.imshow("Gesture Debug", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    sender.close()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    run()