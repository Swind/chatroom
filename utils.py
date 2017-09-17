TYPE = "_http._tcp.local."
FULL_NAME_FORMAT = "{}._http._tcp.local."

def get_full_name(name):
    if not name.startswith("_"):
        name = "_{}".format(name)

    return FULL_NAME_FORMAT.format(name)

def get_resp_event_name(req_event_name):
    return "{}-response".format(req_event_name)