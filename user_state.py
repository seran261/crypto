import time

user_modes = {}
last_signal_time = {}  # (chat_id, symbol) -> timestamp

def set_mode(chat_id, mode):
    user_modes[chat_id] = mode

def get_mode(chat_id):
    return user_modes.get(chat_id, "SCALP")

def can_send(chat_id, symbol, cooldown):
    key = (chat_id, symbol)
    now = time.time()

    if key not in last_signal_time:
        last_signal_time[key] = now
        return True

    if now - last_signal_time[key] >= cooldown:
        last_signal_time[key] = now
        return True

    return False
