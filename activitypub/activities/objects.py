import json
from activitypub.activities import errors

class Object(object):
    attributes = ["type", "id", "name", "to"]
    type = "Object"

    @classmethod
    def from_json(cls, json):
        return Object(**json)

    def __init__(self, obj=None, **kwargs):
        if obj:
            self.__init__(**obj.to_activitystream())
        for key in self.attributes:
            if key == "type":
                continue
            
            value = kwargs.get(key)
            if value is None:
                continue
            
            if isinstance(value, dict) and value.get("type"):
                value = as_activitystream(value)
            self.__setattr__(key, value)

    def __str__(self):
        content = json.dumps(self, default=encode_activitystream)
        return "<{type}: {content}>".format(type=self.type,content=content)

    def to_json(self, context=False):
        values = {}
        for attribute in self.attributes:
            value = getattr(self, attribute, None)
            if value is None:
                continue
            if isinstance(value, Object):
                value = value.to_json()
            # if getattr(value, "__iter__", None):
            #     value = [item.to_json() for item in value]
            values[attribute] = value
        to = values.get("to")
        if isinstance(to, str):
            values["to"] = [to]
        elif getattr(to, "__iter__", None):
            values["to"] = []
            for item in to:
                if isinstance(item, str):
                    values["to"].append(item)
                if isinstance(item, Object):
                    values["to"].append(item.id)

        if context:
            values["@context"] = "https://www.w3.org/ns/activitystreams"
        return values

    def to_activitystream(self):
        return self

class Actor(Object):

    attributes = Object.attributes + [
        "target",

        "preferredUsername",
        "following",
        "followers",
        "outbox",
        "inbox",
    ]
    type = "Actor"

    def send(self, activity):
        res = requests.post(self.inbox, json=activity.to_json(context=True))
        if res.status_code != 200:
            raise Exception

class Person(Actor):

    type = "Person"

#########
# Utils #
#########

ALLOWED_TYPES = {
    "Object": Object,
    "Actor": Actor,
    "Person": Person,
}

def as_activitystream(obj):
    type = obj.get("type")

    if not type:
        msg = "Invalid ActivityStream object, the type is missing"
        raise errors.ASDecodeError(msg)
    
    if type in ALLOWED_TYPES:
        return ALLOWED_TYPES[type](**obj)
                       
    raise errors.ASDecodeError("Invalid Type {0}".format(type))

def encode_activitystream(obj):
    if isinstance(obj, Object):
        return obj.to_json()
    raise errors.ASTypeError("Unknown ActivityStream Type")
                      
