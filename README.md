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

<!-- First Row: Image Left, Text Right -->
<div align="center">
  <table border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
    <tr>
      <td width="30%">
        <img src="https://github.com/user-attachments/assets/5c4a26ea-17aa-4a19-ac9c-8d6283dc80b1" width="100%" alt="Robot Front View">
      </td>
      <td width="70%" align="justify">
        <p>
          Our robot was built to reliably complete all challenges of the RoboCup Junior Rescue Line competition through a combination of computation, custom electronics, and mechanical design. It uses a dual-processor architecture: a Raspberry Pi 5 for high-level logic and AI, and a Raspberry Pi Pico for real-time control of motors and sensors. A Google Coral USB Accelerator enables onboard execution of two YOLOv8 models — one for victim detection and another for identifying the silver evacuation zone — which provide fast and accurate results compared to traditional computer vision.
        </p>
      </td>
    </tr>
  </table>
</div>

<!-- Second Row: Text Left, Image Right -->
<div align="center">
  <table border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse;">
    <tr>
      <td width="70%" align="justify">
        <p>
          The chassis was entirely designed in SolidWorks and 3D printed, with over 70 custom parts and a modular structure that simplifies maintenance. A tilt-mounted wide-angle camera, passive suspension system, and dual-servo rescue arm ensure strong performance across rough terrain. Internally, custom PCBs manage power distribution and sensor integration, keeping the system reliable and clean. Software processes run in parallel for sensing, image processing, and decision-making, supported by a custom HTML interface for real-time monitoring and debugging.
        </p>
      </td>
      <td width="30%">
        <img src="https://github.com/user-attachments/assets/c16464ac-676e-4733-b6ec-849fd3f1d2f7" width="100%" alt="Robot Side View">
      </td>
    </tr>
  </table>
</div>

<!-- Final Paragraph: Full Width -->
<p align="center">
  The robot won the Portuguese National Championship and earned the Best Presentation Award, securing our place in the RoboCup 2025 World Finals.
</p>

---

## 📂 Repository Structure

- `/hardware/` - CAD, schematics, and PCB files
- `/software/` - Source code for the robot
- `/docs/` - Additional documentation

---

## 🧠 Features

- Line following using PID
- Intersection handling
- Ramp detection and compensation
- Victim identification and pickup
- ... (Add your highlights)

---

## 📸 Images

(Add more images below with captions. Example:)

<div align="center">
  <img src="images/line_following.jpg" width="60%" alt="Robot line following demo">
  <p><i>Robot in action during line-following test.</i></p>
</div>

---

## 🤝 Sponsors

(List your sponsors here or link to your sponsorship PDF)

---

## 🔗 Useful Links

- [Official Rescue Line Rules](https://junior.robocup.org/rcj-rescue-line/)
- [Airborne Team Instagram](https://instagram.com/yourteam)
- [Documentation PDF](docs/Airborne_RescueRobot_2025.pdf)
