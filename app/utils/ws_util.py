from flask_socketio import SocketIO
from loguru import logger

socket_client = SocketIO(message_queue="redis://localhost:6379/1")


def send_to_room(user_id: str, message: str, message_type: str = "message"):
    logger.info(f"Sending: {message} to socker room for user_id: {user_id}")
    room = f"user_{user_id}"
    payload = {"data": message, "type": message_type, "user_id": user_id}
    socket_client.emit("stream_message", payload, room=room)


# def send_to_socket(message, user_id, token, message_type="message"):
#     print(1, message)
#     sio = socket_client.Client()

#     try:
#         sio.connect("http://localhost:4001", auth={"token": token})

#         payload = {"data": message, "type": message_type}

#         if user_id:
#             payload["user_id"] = user_id
#             print(f"Sending message to user {user_id}: {message}")
#         else:
#             print(f"Broadcasting message: {message}")

#         sio.emit("stream_message", payload)
#         print("Successfully sent to WebSocket")

#     except Exception as e:
#         print(f"Error sending message to WebSocket: {e}")

#     finally:
#         sio.disconnect()
