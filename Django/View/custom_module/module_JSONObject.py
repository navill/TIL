import json

"""
JSONObject : Json 데이터를 파이썬 객체로 사용할 수 있도록 변환
"""


class JSONObject:
    def __init__(self, json_data):
        self.__dict__ = json_data


if __name__ == '__main__':
    # JSONObject test
    s = {"name": "acme", "price": 1200, "shares": [{"a": "1", "b": "2"}]}  # dict
    t = '{"name": "acme"}'  # json
    converted_json_s = json.dumps(s)  # dict->json
    data = json.loads(converted_json_s, object_hook=JSONObject)
    data2 = json.loads(t, object_hook=JSONObject)
    print(data.name)
    print(data2.name)

    print(json.dumps(s))
    print(json.dumps(s, indent=4))  # pprint를 이용해 출력하거나 indent옵션을 사용하여 json을 깔끔하게 출력할 수 있다.
