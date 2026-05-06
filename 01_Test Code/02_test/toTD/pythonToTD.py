from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.01", 8000)
client.send_message("/bool", True)
client.send_message("/test", 123)
client.send_message("/sample", 456)