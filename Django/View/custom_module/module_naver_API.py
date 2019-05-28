import requests

"""
geo_coding(<str>address) -><json>coordinates: longitude, latitude
: 정확한 주소값을 입력할 경우 해당하는 좌표를 반환하는 함수 - naver api
road_address(<str>address) -> <json>address: 지번주소, 도로명주소
: 일부 주소를 이용해 상세한 지번 주소와 도로명 주소를 출력 - road address api
"""


def geo_coding(address):
    # naver geocoding API - setting
    naver_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=" + address
    custom_headers = {
        "X-NCP-APIGW-API-KEY-ID": 'YOUR-KEY-ID',
        "X-NCP-APIGW-API-KEY": "YOUR-KEY"
    }

    # naver geocoding API - processing
    naver_req = requests.get(naver_url, headers=custom_headers)
    result = (naver_req.json()["addresses"][0]["x"],
              naver_req.json()["addresses"][0]["y"])

    return result


def road_address(address):
    # road address API - setting
    confmkey = "YOUR-CONFIRM-KEY"
    road_url = "http://www.juso.go.kr/addrlink/addrLinkApi.do?keyword=" + address + "&confmKey=" + confmkey + "&resultType=json"
    # # road address API - processing
    road_req = requests.get(road_url)
    result = (road_req.json()["results"]["juso"][0]['jibunAddr'],
              road_req.json()["results"]["juso"][0]['roadAddr'])
    return result
