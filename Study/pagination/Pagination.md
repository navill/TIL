# Django Pagination

[Pagination - documentation](https://docs.djangoproject.com/en/2.2/topics/pagination/)

- django documation에 다음과 같은 예제 코드를 사용해 pagination을 구현할 수 있다

```python
from django.core.paginator import Paginator
from django.shortcuts import render

def listing(request):
    contact_list = Contacts.objects.all()
    paginator = Paginator(contact_list, 25) # Show 25 contacts per page

    page = request.GET.get('page')
    contacts = paginator.get_page(page)
    return render(request, 'list.html', {'contacts': contacts})
```

```html
{% for contact in contacts %}
    {# Each "contact" is a Contact model object. #}
    {{ contact.full_name|upper }}<br>
    ...
{% endfor %}

<div class="pagination">
    <span class="step-links">
        {% if contacts.has_previous %}
            <a href="?page=1">&laquo; first</a>
            <a href="?page={{ contacts.previous_page_number }}">previous</a>
        {% endif %}

        <span class="current">
            Page {{ contacts.number }} of {{ contacts.paginator.num_pages }}.
        </span>

        {% if contacts.has_next %}
            <a href="?page={{ contacts.next_page_number }}">next</a>
            <a href="?page={{ contacts.paginator.num_pages }}">last &raquo;</a>
        {% endif %}
    </span>
</div>
```



### Generic View를 이용한 pagination 구현

```python
# views.py
from .models import FileExam
from django.views.generic import ListView
from django.core.paginator import Paginator

class FileExamListView(ListView):
    model = FileExam
    template_name = "til/exam_list.html"
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super(FileExamListView, self).get_context_data(**kwargs)
        file_objects = FileExam.objects.all()
        paginator = Paginator(file_objects, self.paginate_by)
        page = self.request.GET.get('page')
        file_objects = paginator.get_page(page)
        context['file_objects'] = file_objects
        return context
```

- context : super 함수를 이용하여 요청된 context(self.request에 의해 전달된)를 먼저 context 변수에 할당

- file_objects(1) : model에 정의된 FileExam 객체 호출

- paginator : Paginator 함수를 이용해 객체들과 한 페이지에 출력될 객체의 개수를 지정

- page : GET 메서드로부터 전달받은(.../?page='page값') 페이지 번호

  [image_pagination_1]

- file_objects(2) : Paginator 객체를 이용해 get으로 넘겨받은 페이지 번호에 해당하는 model 객체 할당

- context['file_objects'] : context['file_objects']에 해당 페이지 번호에 호출될 model 객체를 할당하고 이를 반환.



**template에서 전달받은 context data는 다음과 같이 사용된다**.

```html
# list.html
...
<div class="pagination">
        {{file_objects.has_previous}}<br>

        {{file_objects.number}}<br>
        {{file_objects.paginator}}<br>
        {{file_objects.paginator.count}}<br>
        {{file_objects.paginator.num_pages}}<br>
        {{file_objects.paginator.page_range}}<br>

        {{file_objects.has_next}}<br>
</div>
...
```

[image_pagination_2]

- number : 현재 페이지 번호
- paginator : view에서 생성된 Paginator 객체
- paginator.count : paginator가 포함하고 있는 queryset의 갯수
- paginator.num_pages : 총 페이지의 수
- paginator.page_range : 페이지의 범위



###### 현재 페이지 : 2,  게시물의 갯수 : 10개일 경우

```
    {% for num in file_objects.paginator.page_range %}
    {% if file_objects.number == num %}
            <strong>{{ num }}</strong>
    {% else %}
            {{ num }}
    {% endif %}
    {% endfor %}
```

- **output** : 1(3)  **2**(3)  3(3)  4(1) 

###### 현재 페이지 : 4,  게시물의 갯수 : 20개일 경우

```
{% for num in file_objects.paginator.page_range %}
	{% if file_objects.number == num %}
			<strong>{{ num }}</strong>
	{% elif num > file_objects.number|add:'-3' and num < file_objects.number|add:'3'%}                                                                          			{{ num }} 
	{% endif %}
{% endfor %}
```

- **output** : 2  3  **4**  5  6

###### 페이지 이동 아이콘 및 페이지 이동 기능 추가

```
{% if file_objects.has_previous %}
    <a href="?page=1"><<</a>
    <a href="?page={{file_objects.previous_page_number}}"> <</a>
{% endif %}

{% for num in file_objects.paginator.page_range %}
  {% if file_objects.number == num %}
  	  <strong>{{ num }}</strong>
  {% elif num > file_objects.number|add:'-3' and num < file_objects.number|add:'3' %}
	    <a class="pagination-number" href="?page={{ num }}"> {{ num }} </a>
  {% endif %}
{% endfor %}

{% if file_objects.has_next %}
    <a href="?page={{file_objects.next_page_number}}">></a>
    <a href="?page={{file_objects.paginator.num_pages}}">>></a>
{% endif %}
```

[image_pagination_3]

