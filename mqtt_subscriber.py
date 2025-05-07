#!/usr/bin/env python3
"""
Factorio MQTT Subscriber

This script subscribes to MQTT topics from Node-RED and executes
the corresponding actions in the Factorio game.
"""
import time
import json
import logging
import toml
from paho.mqtt import client as mqtt_client
from api.factorio_interface import FactorioInterface

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='factorio_mqtt.log'
)
logger = logging.getLogger('factorio_mqtt')

# Load configuration
config = toml.load("config.toml")
mqtt_config = config.get("mqtt", {})

# Create FactorioInterface instance
factorio = FactorioInterface(config["rcon"]["host"], config["rcon"]["port"], config["rcon"]["password"])

def on_connect(client, userdata, flags, rc):
    """MQTT connect callback"""
    if rc == 0:
        logger.info("Connected to MQTT Broker!")

        client.subscribe(mqtt_config.get("command_topic", "Factorio/Commands"))
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_message(client, userdata, msg):
    """MQTT message callback"""
    try:
        logger.info(f"Received message on topic: {msg.topic}")
        payload = json.loads(msg.payload.decode())
        
        # command decode
        command = payload.get("command")
        params = payload.get("params", {})
        
        if command == "get_player_position":
            result = factorio.get_player_position()
            publish_result(client, command, result)
        
        elif command == "move_player":
            x = params.get("x")
            y = params.get("y")
            result = factorio.move_player(x, y)
            publish_result(client, command, result)
        
        elif command == "place_entity":
            name = params.get("name")
            x = params.get("x")
            y = params.get("y")
            direction = params.get("direction", 0)
            result = factorio.place_entity(name, x, y, direction)
            publish_result(client, command, result)
        
        elif command == "find_entities":
            name = params.get("name")
            entity_type = params.get("type")
            radius = params.get("radius", 10)
            position_x = params.get("position_x")
            position_y = params.get("position_y")
            result = factorio.find_entities(name, entity_type, radius, position_x, position_y)
            publish_result(client, command, result)
        
        elif command == "get_inventory":
            entity = params.get("entity", "player")
            x = params.get("x")
            y = params.get("y")
            result = factorio.get_inventory(entity, x, y)
            publish_result(client, command, result)
        
        elif command == "insert_item":
            item = params.get("item")
            count = params.get("count")
            inventory_type = params.get("inventory_type", "main")
            entity = params.get("entity", "player")
            x = params.get("x")
            y = params.get("y")
            result = factorio.insert_item(item, count, inventory_type, entity, x, y)
            publish_result(client, command, result)
        
        elif command == "remove_item":
            item = params.get("item")
            count = params.get("count")
            entity = params.get("entity", "player")
            x = params.get("x")
            y = params.get("y")
            result = factorio.remove_item(item, count, entity, x, y)
            publish_result(client, command, result)
        
        elif command == "get_available_prototypes":
            result = {
                "entities": factorio.get_available_entities(),
                "items": factorio.get_available_items(),
                "recipes": factorio.get_available_recipes()
            }
            publish_result(client, command, result)
        
        else:
            logger.warning(f"Unknown command: {command}")
            publish_result(client, command, {"error": f"Unknown command: {command}"}, success=False)
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        publish_result(client, "error", {"error": str(e)}, success=False)

def publish_result(client, command, result, success=True):
    """Publish the result of a command"""
    response_topic = mqtt_config.get("response_topic", "Factorio/Responses")
    payload = {
        "command": command,
        "result": result
    }
    client.publish(response_topic, json.dumps(payload))
    logger.info(f"Received result for command: {command}: {result}")

def main():
    """Main function"""
    client_id = mqtt_config.get("client_id", "factorio_subscriber")
    broker = mqtt_config.get("broker", "localhost")
    port = mqtt_config.get("port", 1883)
    username = mqtt_config.get("username", "")
    password = mqtt_config.get("password", "")
    
    client = mqtt_client.Client(client_id=client_id)
    
    if username and password:
        client.username_pw_set(username, password)
    
    # Configure callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect to the MQTT broker
    try:
        client.connect(broker, port)
        logger.info(f"Connected to MQTT broker: {broker}:{port}")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return
    
    # Start the MQTT loop
    client.loop_start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Subscriber stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT broker")

if __name__ == "__main__":
    main()