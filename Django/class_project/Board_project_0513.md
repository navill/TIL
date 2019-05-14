# Boad Project

- 게시판을 만들기위해 model을 다음과 같이 구성한다.
  - Board : 게시판
  - Category : 게시글 종류
  - Document : 게시글 작성 페이지에 필요한 필드를 포함

------

## <Models.py>

### Category - Field

```python
# models.py
class Category(models.Model):
    name = models.CharField(max_length=20)    
    slug = models.SlugField(max_length=30, db_index=True, unique=True, allow_unicode=True)
    description = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['slug']
```

- slug(SlugField)
  -> unique=True :  중복을 허용하지 않음
  -> db_index=True: indexing은 데이터베이스 쿼리 사용 시 일반 검색보다 더 나은 성능을 보인다.

  - SlugField : 이미 가지고 있는 데이터를 이용하여 가독성이 높은 URL을 생성하기 위해 사용
  - 동적으로 slug를 생성하기 위해 다음과 같이 prepopulated_fields를 추가할 수 있다.

  - ```python
    # admin.py
    class DocumentOption(admin.ModelAdmin):
        list_display = ['id', 'author', 'title', ..]
        prepopulated_fields = {'slug': ('title',)}
    ```

- name(CharField)

- description(CharField)

- meta_description(CharField)
  -> meta_description은 SEO(Search Engine Optimization)에 제공하기위해 사용된다.

> **class Meta** : model 단위로 사용되는 option(not fields). 
>
> - 자주 사용되는 옵션
>   - odering : 정렬
>   - db_table : 데이터베이스 이름
>   - verbose_name & verbose_name_plural : 가독성이 향상된 변수의 단복수 이름 

------

### Document - Field

```python
# models.py
class Document(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, db_index=True, unique=True, allow_unicode=True)
    text = models.TextField()
    image = models.ImageField(upload_to='board_images/%Y/%m/%d')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

- category(ForeginKey:Category)
  -> 게시글의 Key 값으로 Category를 설정함으로써 category 별로 게시글을 분류할 수 있다.
- author(ForeignKey:[get_user_model]())
- title(CharField)
- slug(SlugField)
- text(CharField)
- image(ImageField)
- created & updated(auto_now_add & auto_now)

------

## <Views.py>

- 본 프로젝트에서는 generic view가 아닌 funtional view를 사용한다.
- objects manager
- @login_required
- forms.py를 이용한 view control

------

### Form

```python
# froms.py
from django import forms
from .models import Document
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['category', 'title', 'slug', 'text', 'image']
```

- 기본 구조는 Form class 내에 Meta class를 구현한다
- 이 form과 연결될 model(Document)를 변수 ```model``` 에 할당한다.