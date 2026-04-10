# pip install pyserial
# Reference - https://www.youtube.com/watch?v=UeybhVFqoeg
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
portList = []

for one in ports:
    portList.append(str(one))
    print(str(one))

com = input("Select com port for arduino: ")
print(com)

for i in range(len(portList)):
    if portList[i].startswith("/dev/cu.usbserial-" + str(com)):
        use = "/dev/cu.usbserial-" + str(com)
        print(use)

serialInst.baudrate = 115200
serialInst.port = use
serialInst.open()

while True:
    cmd = input("Enter CMD: ")
    serialInst.write(cmd.encode('utf-8'))
    # serialInst.write(cmd)
    print(f"{cmd} write")
    
    if cmd == "exit":
        exit()