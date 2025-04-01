from multiprocessing import Manager

print("MultiProcessing Manager: \t OK")


manager = Manager()

terminate = manager.Value("i", False)

gamepadM1 = manager.Value("i", 1520)
gamepadM2 = manager.Value("i", 1520)
commandToExecute = manager.Value("i", "none") #"none",""

lineCenterX = manager.Value("i", 600)
lineAngle = manager.Value("i", 0.)
line_angle_y = manager.Value("i", -1)
lineDetected = manager.Value("i", False)
turnReason = manager.Value("i", 0)
redDetected = manager.Value("i", False)
silverValue = manager.Value("i", 0) # 0 = Line, 1 = Silver

ballDistance = manager.Value("i", -1)
ballWidth = manager.Value("i", -1)
ballType = manager.Value("i", "none") # "none"; "silver ball"; "black ball"

isCropped = manager.Value("i", False)
lineCropPercentage = manager.Value("i", 0.6)
onIntersection = manager.Value("i", False)
turnDirection = manager.Value("i", "straight") # "straight", "left", "right", "uTurn"
objective = manager.Value("i", "follow_line")  # "follow_line"; "zone"; "debug"
line_status = manager.Value("i", "line_detected")  # "line_detected"; "gap_detected"; "gap_avoid"; "obstacle_detected"; "obstacle_avoid"; "obstacle_orientate"; "check_silver"; "position_entry"; "position_entry_1"; "position_entry_2"; "stop"
zoneStatus = manager.Value("i", "notStarted")  # "notStarted"; "begin"; "entry"; "findVictims"; "pickup_ball"; "deposit_red"; "deposit_green"; "exit"
LOPstate = manager.Value("i", 0)
# WARNING -- SHOULD BE NOT STARTED


status = manager.Value("i", "Stopped")
saveFrame = manager.Value("i", False)
