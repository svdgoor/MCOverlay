from pynput.keyboard import Key, Controller
import pyperclip
import time
controller = Controller()
class CommandSender:
    def who():
        """Sends a who command
        """
        CommandSender.type("/who")
        
    def leave():
        """Sends a leave command
        """
        CommandSender.type("/l")
        
    def pwarp():
        """Sends a p warp command
        """
        CommandSender.type("/p warp")

    def type(line: str):
        """Writes a line using the virtual keyboard

        Args:
            line (str): The line to write
        """
        print("Sending command: {}".format(line))
        pyperclip.copy(line)
        controller.release(Key.shift)
        controller.press("t")
        controller.release("t")
        time.sleep(0.1)
        controller.press(Key.ctrl)
        controller.press("v")
        time.sleep(0.1)
        controller.release(Key.ctrl)
        controller.release("v")
        time.sleep(0.1)
        controller.press(Key.enter)
        controller.release(Key.enter)