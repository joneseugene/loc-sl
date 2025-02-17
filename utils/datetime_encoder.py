import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

# Example data containing a datetime object
data = {
    "name": "John",
    "timestamp": datetime.now()
}

# Serialize using the custom encoder
json_data = json.dumps(data, cls=DateTimeEncoder)
