import paho.mqtt.client as mqtt

def on_connect(clients, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("your/command/channel")
    
def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}; {msg.payload}")
    
    
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
print("Listenning Forever")
try:
    client.loop_forever()
except:
    print("Something Happened Connecting to the Broker!")
    