import pickle
import base64


def dumps(param_dict):
    dict_bytes = pickle.dumps(param_dict)
    str_bytes = base64.b64encode(dict_bytes)
    return str_bytes.decode()


def loads(param_str):
    str_bytes = param_str.encode()
    dict_bytes = base64.b64decode(str_bytes)
    return pickle.loads(dict_bytes)
