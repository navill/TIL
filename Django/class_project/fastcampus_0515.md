# FastCampus_0515

```python
from django.db.models import F
from board.models import Document
```

```Document.objects.filter(title__icontains='search keyword')``` : title 필드에 해당하는 **값**(string type : 'search keyword')을 filtering할 때 사용된다. 

> Outlink : 다른 곳에서 링크를 걸거나 검색을 할 경우 keyword와 본문의 관련도가 높다고 판단되어 검색 우선 순위를 높일 수 있다.

- python code보다 db를 검색하는 것이 훨씬 빠르다.
  - python code를 이용해 F를 구현할 수 있지만 F를 이용해 필드 변수를 검색할 수 있다. 

```Document.objects.filter(text__icontains=F('title'))``` 

```Document.objects.filter(text__icontains=F('author__username'))``` :  title & author의 username **field**에 들어있는 문자열을 이용해 필터링한다.

> if구문은 db에 부담을 많이 주기 때문에 잘 사용하지 않는다.
> 따라서 chaining을 사용한다.

```python
q = Document.objects.filter(author__username='name')
q = q.filter()
q = q.filter()  # 3번의 filter
# 각 filter 구문은 평가(실제 db를 불러오는 것) 전 까지 실행되지 않는다.
```





------

### Logger

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'  # output to console
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',  # 반드시 DEBUG = True
        }
    }

}
```

또는 python code 내에

```python
import logging
l=logging.getLogger('django.db.')
```





------

### Select_related

```python
object_list = Document.objects.all() # query access 1
for object in object_list:  # 
		print(object.author.username)  # query access * number of author
```

- Document object를 불러올 때 마다 db에 많은 부담을 준다

```python
object_list = Document.objects.select_related('auhtor').all()  # query access 1
for object in object_list:
		print(object.author.username)
```

##### Category

| id   | name |
| ---- | ---- |
| 1    | a    |
| 2    | b    |
| 3    | c    |

##### Document

| id   | title | category_id |
| ---- | ----- | :---------: |
| 1    | 가    |      1      |
| 2    | 나    |      1      |
| 3    | 다    |      3      |

##### Join category & document : query access를 최소화 하기 위해 사용

| id   | title | category_id | name |
| ---- | ----- | ----------- | ---- |
| 1    | 가    | 1           | a    |
| 2    | 나    | 1           | a    |
| 3    | 다    | 3           | c    |

- inner join : 존재하는 키값들끼리 연결(교집합)
  - inner join - category_id(1)를 할 경우 id가 1, 2를 가진 값이 출력된다.
- outer join : 없는 키값들끼리 연결(left, right 부분 집합)

- full outer join: 전체 값 연결

------

### prefetch_related

```
Document.objects.prefetch_related('author').all()
```

- select_related -> join query를 만들어서 한번에 데이터를 불러온다.
  - ForeignKey까지만 묶을 수 있다.
    - ManyToMany를 실행할 경우, join이 실행될 때 마다 중복되는 필드를 db연산이 모두 끝날 때까지 호출된다 -> db에 부하를 가져온다.

- prefetch_related -> Document와 Category를 불러서 python 코드 단에서 한번에 병합
  - ForeignKey를 포함한 ManyToMany를 지원한다.
- select_related와 prefetch_related를 사용하지 않을 경우 참조 테이블(foreignkey와 같이 다른 테이블에 묶인 테이블)에 대한 데이터 질의를 항상 실행해야한다. 이는 불필요한 데이터베이스 access를 초래하고 DB에 부하를 주게 된다.