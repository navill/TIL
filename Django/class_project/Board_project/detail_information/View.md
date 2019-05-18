# View.py

### def document_list(request)

**<주요 기능>**

- pagiation - 화면에 출력될 객체 리스트 및 page 구현
- search - Q를 이용한 타입과 키워드 검색 구현
- redering(document_list.html)
  - object_list : documents
  - total_page : total_page
  - page_range : page_range

##### pagination

```python
page = int(request.GET.get('page', 1))
paginated_by = 3
  ...

total_count = len(documents)
total_page = math.ceil(total_count / paginated_by)
page_range = range(1, total_page + 1)

start_index = paginated_by * (page - 1)
end_index = paginated_by * page

documents = documents[start_index:end_index]
```

- request.GET.get('page', 1) : 첫 화면 접속 시 query set 'page'가 없을 경우 default를 page인가한다.
  만일 query set에 page가 포함될 경우(사용자가 page이동을 위해 page number를 클릭) 그 페이지 번호를 page 변수에 인가한다.
- documents[start_index:end_index] : 화면에 출력될 리스트를 list slicing을 이용해 filtering 한다. 

##### Search with Q

```python
a = Q(title__icontains=search_key) | temp_q = Q(author__icontains=search_key)
```

- 변수 a에 title이름 속에 keyword(search_key) 포함 여부와 author에 keyword의 포함 여부를 'or'연산을 통해 할당한다.

  ##### from django.db.models import Q

  - 검색 옵션의 집합 연산을 위해 사용된다.

    ```first_q = Q(query options)``` : Q 객체 생성

    ```first_q|second_q``` : or 연산

    ```first_q & second_q``` : and 연산

    ```~first_q``` : not

------

### def document_create(request)

- @login_required - 내부에 구현된 is_authenticated에 의해 사용자의 로그인 여부 확인. 로그인(is_authenticated==True)일 때 게시글 작성 가능 하도록 구현.

- request 

  ```mermaid
  graph LR
  client(client) --> |request| views.py
  views.py(document_create) --> |request.POST/request.FILES|forms.py
  forms.py(DocumentForm)
  
  ```

  - request.method=='POST'
  - requset.FILES(이미지 파일)는 사용자가 server로 보낸 request에 포함되어있다. 이를 DocumentForm의 초기화값으로 인가한 후 객체를 생성한다.

  - 게시물 작성 페이지는 빈 페이지를 보여야하기 때문에 if를 통해 사용자에 의한 POST 전(빈페이지), 후(작성된 정보 전송)로 분기한다.

  - DocumentForm 객체인 form은 document_create 함수의 연산을 마친 후 rendering 된다.

------

### def document_update(request, document_id)

- ```path('update/<int:document_id>/', document_update, name='update')``` : urls.py에 다음과 같이 정의되어있으며, client의 request.POST에 의해 document_id가 document_update 함수에 전달된다.

- ```intance=document``` : 업데이트 페이지는 기존에 작성된 글이 화면에 출력되어야 하기 때문에 instance에 Document 객체(post에 의해 전달된 수정될 게시글)인 document 변수를 할당한다.
  - BaseModelForm에 다음과 같이 구현되어있다.
    - 만일 instance가 none일 경우 초기화된 instance 객체 생성
    - instance가 있을 경우 해당 객체 생성
- document_create와 마찬가지로 if 분기를 통해 POST 전, 후로 기존에 작성된 페이지를 화면에 출력할지 수정된 정보를 전송할지 결정한다.
  - form에는 instance=document 인자를 받은 DocumentForm이 할당된다(수정되어야할 글이 화면에 출력).

------

### def document_detail(request, document_id)

**<주요 기능>**

- 해당 게시글에 댓글 기능

  ```mermaid
  graph LR
  client(client) -->|request, document_id|detail(document_detail)
  client(client) -->|comment| CF(CommentForm)
  
  
  ```

  - 댓글 기능을 view에서 처리하지 않고 form에서 처리하기 위해 forms.py에 CommentForm을 구현하였다.
  - detail view는 게시글과 댓글 form을 화면에 출력한다.
  - document 객체, 기존에 작성된 comments, 그리고 댓글 작성을 위한 comment_form이 html에 렌더링 된다.











