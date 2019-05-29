from django.shortcuts import render
from django.db.models import Q

from room.models import Media

from json_Test import coord_to_json, center_from_coord
import requests


def create_address(address):
    naver_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query=" + address
    custom_headers = {
        "X-NCP-APIGW-API-KEY-ID": 'b4wnbq4cd7',
        "X-NCP-APIGW-API-KEY": "8o4ERGCLrQgfFb9qoXRmJELLQBI6N3kHxUjELMXX"
    }
    # road address API - setting
    confmkey = "U01TX0FVVEgyMDE5MDUyMzAwNDAwMzEwODc0Nzc="
    road_url = "http://www.juso.go.kr/addrlink/addrLinkApi.do?keyword=" + address + "&confmKey=" + confmkey + "&resultType=json"

    # # requests of both API
    naver_req = requests.get(naver_url, headers=custom_headers)
    road_req = requests.get(road_url)
    result = (road_req.json()["results"]["juso"][0]['jibunAddr'],
              road_req.json()["results"]["juso"][0]['roadAddr'],
              naver_req.json()["addresses"][0]["x"],
              naver_req.json()["addresses"][0]["y"]
              )
    return result


def search(request):
    cb_list = request.GET.getlist('cb', None)
    search_key = request.GET.get('search_key', None)

    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)

    search_p = None
    obj_list = None
    if not (search_key or cb_list or min_price or max_price):
        obj_list = Media.objects.all()
        return render(request, 'room/search_list.html',
                      {
                          'object_list': obj_list,
                      }
                      )

    if min_price or max_price:
        dic = {'만': 1, '억': 10000, }
        if min_price and not max_price:
            price_min_num = int(min_price[:-1])
            price_min_str = dic[min_price[-1]]
            min_price = price_min_num * price_min_str
            search_p = Q(price_real__gte=min_price)
            obj_list = Media.objects.filter(search_p)

        elif max_price and not min_price:
            price_max_num = int(max_price[:-1])
            price_max_str = dic[max_price[-1]]
            max_price = price_max_str * price_max_num
            search_p = Q(price_real__lte=max_price)

            obj_list = Media.objects.filter(search_p)

        # 둘다 있는 경우
        else:
            price_min_num = int(min_price[:-1])
            price_min_str = dic[min_price[-1]]
            min_price = price_min_num * price_min_str

            price_max_num = int(max_price[:-1])
            price_max_str = dic[max_price[-1]]
            max_price = price_max_str * price_max_num

            search_p = Q(price_real__gte=min_price) & Q(price_real__lte=max_price)
            obj_list = Media.objects.filter(search_p)

    json_result = {"coord": list()}
    if search_key and search_p:
        search_p = Q(address__icontains=search_key) | Q(name__icontains=search_key)
        obj_list = obj_list & Media.objects.filter(search_p)
        # address_results = list()
        for object in obj_list:
            coord_json = create_address(object.address)[2:4]
            coord_to_json(json_result, coord_json)
        a = json_result.update(center=center_from_coord(json_result))
        print(a)

    else:
        if search_key or not obj_list:
            search_p = Q(address__icontains=search_key) | Q(name__icontains=search_key)
            obj_list = Media.objects.filter(search_p)
            for object in obj_list:
                coord_json = create_address(object.address)[2:4]
                coord_to_json(json_result, coord_json)
            center_value = json_result.update(center=center_from_coord(json_result))

    if cb_list:
        temp_p = search_p & Q(select__icontains=cb_list[0]) if search_key else Q(select__icontains=cb_list[0])
        length = len(cb_list)
        if length >= 2:
            for i in range(1, length):
                temp_p &= Q(select__icontains=cb_list[i])

        if not obj_list:
            obj_list = Media.objects.filter(temp_p)

        else:
            obj_list = obj_list & Media.objects.filter(temp_p)
    return render(request, 'room/search_list.html',
                  {
                      'object_list': obj_list, 'json_result': json_result
                  })
