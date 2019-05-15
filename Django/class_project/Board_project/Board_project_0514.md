# fast_0514

```python
    documents = documents[:3] 
```

QuerySet 객체를 슬라이싱할 때 [시작번호:끝번호]

------

**keyword를 검색할 때**

1. db query를 이용해 검색(filter를 이용) - 'like'
2. python의 순환문을 이용해 all()으로부터 가져온 text를 검색

- 일반적인 상황에서 db가 조금 더 빠르지만, db의 리소스 부하를 가져온다.

------

##### Search에 키워드를 입력할 경우 - text matching 기반

##### [ElasticSearch(search engine)](https://www.elastic.co/kr/products/elasticsearch) : 단순 쿼리문을 이용한 검색은 한계가 있기 때문에 검색엔진을 추가하여 검색 성능을 향상 시킬 수 있다.

1. 검색어의 유효성 검사
2. filter method를 이용한 검사 
   1. 어떤 항목을 검색할지?
      ex) 제목? 작성자? 등..
   2. 어떤 옵션을 이용해 검색할지?
      ex) 시작점? 대소문자 구분해서? 등..

```python
Document.objects.filter(pk=1)
# -> pk=1에 해당하는 데이터 출력
Document.objects.filter(pk=1, title='test')
# -> pk=1과 title이 'test'인 데이터 출력
Document.objects.filter(title__startswith='11')
# -> filter(필드이름__옵션) 구조로 사용된다.
```

- filter 옵션 - 현재 local filed만 검색할 수 있다.

  -> 단순 옵션으로 ForeignKey, ManyToMany 등은 검색할 수 없기 때문에 다음과 같은 구조를 사용한다.
  ```foreignkey(filedname)__attibute(model_fieldname)__option``` 

  ```foreignkey(fieldname)__attribute(model_fieldname)```

  

  ```__startswith & __endswith``` : 시작 & 끝에 해당하는 문자 검색
  ```__iexact``` : 대소문자 구문 없이 검색
  ```___contains```: 문자 내에 해당하는 keyword 검색

  ```target__gt=value & target__gte=value``` : target이 value보다 크다(크거나 같다)

  ```target__lt=value & target__lte=value``` : target이 value보다 작다(작거나 같다)



```python
def document_list(request):
    search_key = request.GET.get('search_key', None)
    if search_key:
        documents = get_list_or_404(Document, title__icontains=search_key)
    else:
        documents = get_list_or_404(Document)
    total_count = len(documents)  # 전체 페이지 수
    total_page = math.ceil(total_count / paginated_by)
    page_range = range(1, total_page + 1)

    start_index = paginated_by * (page - 1)
    end_index = paginated_by * page
    documents = documents[start_index:end_index]  
    return render(request, 'board/document_list.html',
                  {'object_list': documents, 'total_page': total_page, 'page_range': page_range})

```

- get_list_or_404(Model, filter_options) : filter가 적용된 모델 객체를 반환하거나, 조건이 충족될 경우 page not found 404 에러를 화면에 출력

- search_key = request.GET.get('search_key', None) : template에 정의된 name으로부터 keyword값을 받는다
  -> 단순 text 형태의 keyword값을 수신하기 때문에 GET을 사용한다.
  -> GET은 queryset이 URL에 출력된다(POST는 body에 추가되어 사용자에게 노출되지 않는다).
  ```http://127.0.0.1:8000/?search_key=e```

##### from django.db.models import Q

- 검색 옵션의 집합 연산을 위해 사용된다.

  ```first_q = Q(query options)```

  ```first_q|second_q``` : or 연산

  ```first_q & second_q``` : and 연산

  ```~first_q``` : not

> **Q객체를 사용할 때는 일반 field에 대한 옵션을 Q 뒤에 위치 시켜야한다.**
>
> ```Doc.objects.filter(third_q, first_q | second_q, title__contains='1')```

- 사용자로부터 데이터를 전달받으려면(GET, POST) form 내에 있어야한다. 

- input tag는 단순히 데이터를 받는 공간
- GET.get(a,b,c) -> return 시, c만 반환된다.
- GET.getlist(a,b,c) -> return 시, a,b,c가 반환된다.

------

##### Check box의 default 설정 방법

1. template에서 'checked'  설정
2. backend에서 'if not search_type:' 조건을 통해 강제로  query를 지정

과제1. document, category, board 모델 확장

과제2. 검색 페이지 구현(Board, Category, Document)

과제3. 모델 : 이름, 전화번호, 메모, 검색 기능

------

##### Search 기능을 향상 시키기 위해 다음과 같은 기능을 익혀야한다.

- F : 컬럼 참조
- Join
- select_related -> DB에 부담을 줄지 서버에 부담을 줄지
- prefetch_related

**DB query의 최적화가 가장 높은 효율을 보이고 이후 인프라, 소스코드 최적화를 통해 추가적인 퍼포먼스 향상을 기대할 수 있다.**

