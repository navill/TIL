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

- request.GET.get('page', 1) : 첫 화면 접속 시 query set 'page'가 없을 경우 default(<int>1)를 page 변수에 인가한다.
  만일 query set에 'page=(number)'이 포함될 경우(사용자가 page이동을 위해 page number를 클릭) 그 페이지 번호를 page 변수에 인가한다.
- documents[start_index:end_index] : 화면에 출력될 리스트를 list slicing을 이용해 filtering 한다. 

##### Search with Q

```python
a = Q(title__icontains=search_key) | temp_q = Q(author__icontains=search_key)
```

- 변수 a에 title에 포함된 문자열 중 keyword(search_key)문자의 포함 여부와 author에 keyword의 포함 여부를 'or'연산을 통해 할당한다.

  ##### from django.db.models import Q

  - 검색 옵션의 집합 연산을 위해 사용된다.

    ```first_q = Q(query options)``` : Q 객체 생성

    ```first_q|second_q``` : or 연산

    ```first_q & second_q``` : and 연산

    ```~first_q``` : not

------

### def document_create(request)

- @login_required - 내부에 구현된 is_authenticated에 의해 사용자의 로그인 여부 확인. 로그인(is_authenticated==True) 되었을 때 게시글 작성 가능 하도록 구현.

- request 

  ![스크린샷 2019-05-18 오후 5.20.51](https://github.com/navill/TIL/blob/master/Django/class_project/Board_project/detail_information/board_project_image/view/board_project.001.png)

  - request.method=='POST'
  - requset.FILES(이미지 파일)는 사용자가 server로 보낸 request에 포함되어있다. 이를 DocumentForm의 초기화값으로 인가한 후 객체를 생성한다.
- 게시물 작성 페이지는 빈 페이지를 보여야하기 때문에, if를 통해 사용자에 의한 POST 전(빈페이지), 후(작성된 정보 전송)로 분기한다.
  - DocumentForm 객체인 form은 document_create 함수의 연산을 마친 후 rendering 된다.

###### Form

> **Form의 네 가지 상태**
>
> - **Empty form (unfilled form)**: 비어있는 초기 form 형태(unbound)
> - **Filled form**: 사용자가 form에 데이터를 입력한 상태(bound)
>   - Form.is_bound -> boolean 을 통해 확인할 수 있다.
> - **Submitted form with errors**: form에 데이터를 입력하였지만 올바르지 않은 접근 또는 입력(invalid)
> - **Submitted form without errors**: form에 올바른 접근과 유효한 데이터를 입력(valid)
>   - Form.is_valid -> boolean 을 통해 확인할 수 있다.
>
> **form은 is_bound와 is_valid에 의해 form의 작동 여부를 판단 할 수 있으며, 이를 통해 기능을 분기 할 수 있다.**

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

  ![스크린샷 2019-05-18 오후 5.21.35](https://github.com/navill/TIL/blob/master/Django/class_project/Board_project/detail_information/board_project_image/view/board_project.002.png)

  - 댓글 기능을 view에서 처리하지 않고 form에서 처리하기 위해 forms.py에 CommentForm을 구현하였다.
  - document_detail view는 게시글과 댓글 form을 화면에 출력한다.
  - document 객체, 기존에 작성된 comments, 그리고 댓글 작성을 위한 comment_form이 html에 렌더링 된다.

  ##### forms.CommentForm(forms.ModelForm)

  ```python
  class CommentForm(forms.ModelForm):
      class Meta:
          model = Comment
          fields = ['text']
  
      def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.fields['text'].label = "댓글"
          self.fields['text'].widget = forms.TextInput()
          self.fields['text'].widget.attrs = {'class': "form-control", 'placeholder': "댓글을 입력하세요"}
  ```

  

> widget : HTML 입력 요소를 표현하기 위해 사용된다.
>
> - HTML rendering, 위젯과 연관된 GET/POST(context type)의 데이터를 추출할 수 있다.
> - forms.CommentForm에서 사용된 위젯은 다음과 같이 구성할 수 있다.
>
> ```self.fields['text'] = forms.CharField(widget=forms.TextInput(attrs={'class: "form-control', 'placeholder': "댓글을 입력하세요"}))```

> <참고>
> Widgets should not be confused with the [form fields](https://docs.djangoproject.com/ko/2.2/ref/forms/fields/). Form fields deal with the logic of input validation and are used directly in templates. Widgets deal with rendering of HTML form input elements on the web page and extraction of raw submitted data. However, widgets do need to be [assigned](https://docs.djangoproject.com/ko/2.2/ref/forms/widgets/#widget-to-field) to form fields.

------

### def document_delete()





------

### def comment_create()

**<주요 기능>**

- 게시글 하단에 기존에 생성된 댓글 리스트 출력

  ![board_project.001](https://github.com/navill/TIL/blob/master/Django/class_project/Board_project/detail_information/board_project_image/view/board_project.003.jpeg)

- document_detail.html은 화면에 보여질 게시글(Document: document), form에 구성된 댓글 입력 창(CommentForm: [comment_form](#formscommentformformsmodelform)), 기존에 입력된 댓글 리스트(document.comments.all)로부터 데이터를 전달받는다.

- request.POST(입력 버튼 클릭 시 발생한 Post)에는 작성자 및 작성 내용을 포함한다.
  
- 이러한 정보는 댓글 입력이 완료되었을 때, CommentForm의 객체에 전달되고 유효성 검사([is_valid](#form)) 후 save함수를 통해 db에 저장된다. 
  if 분기를 통해 is_valid가 False일 경우 기존의 document로 redirect 된다.
  
- 모든 과정이 완료되면 게시글, 빈 댓글 입력창, 새로 작성하여 db에 저장된 댓글을 포함한 댓글 리스트가 화면에 출력된다.

> 구조 설계 시, 기능 및 구조를 고려하여 여러 view(document_detail, comment_create)에서 데이터를 가공한 후 하나의 template(document_detail)에 전달 할 수 있다.

------

### def comment_update()

**<주요 기능>**



------

### def comment_delete()

**<주요 기능>**



------

