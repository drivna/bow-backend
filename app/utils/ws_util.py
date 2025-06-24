import socketio

def send_to_socket(message, user_id, token, message_type="message"):
    print(1, message)
    sio = socketio.Client()

    try:
        sio.connect("http://localhost:4001", auth={"token": token})

        payload = {
            "data": message,
            "type": message_type
        }

        if user_id:
            payload["user_id"] = user_id
            print(f"Sending message to user {user_id}: {message}")
        else:
            print(f"Broadcasting message: {message}")

        sio.emit("stream_message", payload)
        print("Successfully sent to WebSocket")

    except Exception as e:
        print(f"Error sending message to WebSocket: {e}")

    finally:
        sio.disconnect()
