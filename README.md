<div align="center">
  <a href="https://github.com/JamesBond6873">
    <img src="https://img.shields.io/badge/Contributor-JamesBond6873-blue" alt="JamesBond6873">
  </a>
  
  <a href="https://github.com/eumesmodefacto">
    <img src="https://img.shields.io/badge/Contributor-eumesmodefacto-blue" alt="eumesmodefacto">
  </a>
</div>

<br/>

<p align="center">
  This is the repository for <strong>Airborne</strong>, a Portuguese robotics team that participated in the
  <a href="https://junior.robocup.org/">RoboCup Junior</a> sub-league
  <a href="https://junior.robocup.org/rcj-rescue-line/">Rescue Line</a>.
</p>

# About the Competition
<p align="center"><i>
  "The land is too dangerous for humans to reach the victims. Your team has been given a challenging task. The robot must be able to carry out a rescue mission in a fully autonomous mode with no human assistance. The robot must be durable and intelligent enough to navigate treacherous terrain with hills, uneven land, and rubble without getting stuck. When the robot reaches the victims, it has to gently and carefully transport each one to the safe evacuation point where humans can take over the rescue. The robot should exit the evacuation zone after a successful rescue to continue its mission throughout the disaster scene until it leaves the site. Time and technical skills are essential!"
</i></p>

<div align="center">
  <img src="https://github.com/user-attachments/assets/a0c5800d-fcd0-47f1-990c-3d6951691d1c" style="width:70%;"/>
</div>

# About the Robot

<!-- First block: Image on the left -->
<img src="https://github.com/user-attachments/assets/5c4a26ea-17aa-4a19-ac9c-8d6283dc80b1" align="left" style="width:25%; margin-left:20px; margin-bottom:10px;" />

<p align="justify">
  Our robot was built to reliably complete all challenges of the RoboCup Junior Rescue Line competition through a combination of computation, custom electronics, and mechanical design. It uses a dual-processor architecture: a Raspberry Pi 5 for high-level logic and AI, and a Raspberry Pi Pico for real-time control of motors and sensors. A Google Coral USB Accelerator enables onboard execution of two YOLOv8 models, one for victim detection and another for identifying the silver evacuation zone, which provide fast and accurate results compared to traditional computer vision.
</p>

<br/>

<!-- Second block: Image on the right -->
<img src="https://github.com/user-attachments/assets/c16464ac-676e-4733-b6ec-849fd3f1d2f7" align="right" style="width:25%; margin-right:20px; margin-bottom:10px;" />

<p align="justify">
  The chassis was entirely designed in SolidWorks and 3D printed, with over 70 custom parts and a modular structure that simplifies maintenance. A tilt-mounted wide-angle camera, passive suspension system, and dual-servo rescue arm ensure strong performance across rough terrain. Internally, custom PCBs manage power distribution and sensor integration, keeping the system reliable and clean, with a much lower risk of lose wires. Software processes run in parallel for serial communication between boards, image processing, and control/decision-making, supported by a custom HTML/Websocket interface for real-time monitoring and debugging.
</p>

<br/>

<p align="center">
  As required by the competition <a href="https://github.com/JamesBond6873/Airborne_Rescue_Line_2025/blob/main/Documents/Rules/000_RoboCup_Junior_Rescue_Line_Rules_2025.pdf">rules</a>, in addition to this GitHub Repository, we created detailed documentation of the robot and our development process in the form of a <a href="https://github.com/JamesBond6873/Airborne_Rescue_Line_2025/blob/main/Documents/Final%20Rubrics/00_Airborne_TDP_RoboCup_Rescue_Line_2025.pdf">Technical Description Paper</a>, a <a href="https://github.com/JamesBond6873/Airborne_Rescue_Line_2025/blob/main/Documents/Final%20Rubrics/01_Airborne_Poster_RoboCup_Rescue_Line_2025.pdf">Technical Poster</a>, and a <a href="https://github.com/JamesBond6873/Airborne_Rescue_Line_2025/blob/main/Documents/Final%20Rubrics/02_Airborne_Video_RoboCup_Rescue_Line_2025_Compressed.mp4">Presentation Video</a>.
</p>




## 📂 Components

- Raspberry Pi 5 8GB Ram
- Raspberry Pi Pico
- Google Coral USB Accelerator
- Raspberry Pi Camera Module V3 Wide
- 5x VL53L0X ToF
- ICM-20948 9DOF IMU
- TCA9458 Multiplexer
- 4x Home-made Silicone Wheels
- 4x 12V 77RPM DC Geared Motors
- 4x 3S ESCs
- 6x SG90 MicroServos
- PCA9685 Servo Driver
- 2x Custom Led Bar PCB
- DRV8833 Power Driver
- Gens Ace 3S 2700mAh Lipo Battery
- D24V50F5 Step Down
- D36V28F5 Step Down


## 🧠 Repository Structure

Text

Text

Text


# 🔗 Useful Links

- [Official Rescue Line Rules](https://junior.robocup.org/rcj-rescue-line/)
- [Airborne Team Instagram](https://instagram.com/yourteam)
- [Documentation PDF](docs/Airborne_RescueRobot_2025.pdf)


---

# 🤝 Sponsors

(List your sponsors here or link to your sponsorship PDF)

