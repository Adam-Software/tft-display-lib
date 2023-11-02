from robot_eye_display import RobotEyeDisplay

robot_eye_display = RobotEyeDisplay()

gif_paths_R = [
    'ExampleGIF/Смущен/LEFT/Adam-Black-eyes-смущен-LEFT.gif'
]
gif_paths_L = [
    'ExampleGIF/Смущен/RIGHT/Adam-Black-eyes-смущен-RIGHT.gif'
]
robot_eye_display.run(gif_paths_R, gif_paths_L)
