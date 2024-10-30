


def notify_user(user, product, position):
    # Logic to send SMS notification
    message = f"You are at position {position} in the queue for {product.name}. Please complete your order within 4 hours."
    # Use your SMS service API to send the message