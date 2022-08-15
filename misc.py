import random
import socket
import string

ALPHANUM = string.ascii_lowercase + string.digits


def get_col(arr, col):
    return map(lambda x: x[col], arr)


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def gen_uuid():
    return ''.join(random.choices(ALPHANUM, k=8))
