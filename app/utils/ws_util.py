def send_to_socket(message):
    print(1, message)
    """
    A generic function to send any message to the WebSocket server (running on port 4001).
    """
    try:
        # Emit message to WebSocket server
        from app.main import socket_client

        socket_client.emit("stream_message", {"data": message})
        print(f"Sent to WebSocket: {message}")
    except Exception as e:
        print(f"Error sending message to WebSocket: {e}")
