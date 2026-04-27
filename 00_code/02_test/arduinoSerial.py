# pip install pyserial
# Reference - https://www.youtube.com/watch?v=UeybhVFqoeg
import serial
import serial.tools.list_ports
import time
import threading

ports = serial.tools.list_ports.comports()
portList = []

for one in ports:
    portList.append(str(one))
    print(str(one))

com = input("Select com port for arduino: ").strip()
print(com)

use = None

for i in range(len(portList)):
    if portList[i].startswith("/dev/cu.usbserial-" + str(com)):
        use = "/dev/cu.usbserial-" + str(com)
        print(use)
        break

if use is None:
    print("Arduino Not FOund")
    exit()

ser = serial.Serial(use, 115200, timeout=0.1)
time.sleep(2)

running = True

def write_serial():
    global running
    
    while running:
        cmd = input("Enter CMD: ").strip()
        
        if cmd  == "exit":
            running = False
            break
        if cmd:
            ser.write((cmd+"\n").encode('utf-8'))
            print(f"{cmd} write")
writer_thread = threading.Thread(target=write_serial, daemon = True)
writer_thread.start()

while running:
        if ser.in_waiting > 0:
            reply = ser.readline().decode("utf-8", errors="ignore").strip()
            if reply:
                print("from Arduino:", reply)

# while True:
#     if ser.in_waiting > 0:
#         reply = ser.readline().decode('utf-8', errors='ignore').strip()
#         if reply:
#             print("from Arduino: ", reply)        

    # cmd = input("Enter CMD: ")
    # ser.write((cmd+"\n").encode('utf-8'))
    # # ser.write(cmd)
    # print(f"{cmd} write")
    
    # if cmd == "exit":
    #     break
    
