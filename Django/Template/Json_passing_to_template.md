# View에서 data를 javascript로 패싱할 때 발생하는 에러

네이버 지도 API를 사용하면서 다음과 같은 에러를 일으켰다.

- view에서는 json타입으로 데이터를 저장한 후 'json_result'라는 변수로 할당하였다.
- 이를 context-type으로 view로 전달한다.

function-render in views.py

```python
 'object_list': obj_list, 'json_result': json_result
```

javascript in template(detail_page.html)

```javacript
    var temp_test = {{json_result}};
```

result in debug page

![image-20190526200034146](/Users/jh/Library/Application Support/typora-user-images/image-20190526200034146.png)



### Solution.1 

**function-render in views.py**

```python
 'object_list': obj_list, 'json_result': json.dumps(json_result)
```

**javascript in template(detail_page.html)**

```javacript
    var temp_test = JSON.parse("{{json_result|escapejs}}");
```

**result in debug page**

![image-20190526195523790](/Users/jh/Library/Application Support/typora-user-images/image-20190526195523790.png)



### Solution.2

**function-render in views.py**

```python
 'object_list': obj_list, 'json_result': json_result
```

**javascript in template(detail_page.html)**

```javascript
    var temp_test = {{json_result | safe}};
```

**result in debug page**

![image-20190526195837826](/Users/jh/Library/Application Support/typora-user-images/image-20190526195837826.png)





