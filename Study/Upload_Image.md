# Upload Image File

**models.py**

```photo = models.ImageField(upload_to='photos/%Y/%m/%d')``` : 이미지 파일을 upload_to에 할당된 주소에 저장하도록 모델을 설정해야한다.

> django에서 ImageField를 사용하려면 반드시 pillow 모듈을 설치해서 사용해야 한다.



**settings.py**

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

MEDIA_URL : 파일을 브라우저에 제공할 때 필요한 가상의 URL

	- MEDIA_URL은 서버 내부 폴더 구조를 숨길 수 있기 때문에 보안상 필요하다.

MEDIA_ROOT : local에 저장될 파일의 경로

- 각 앱에서 업로드하는 이미지는 MEDIA_ROOT에 지정된 경로에 저장된다.
- root directory의 'media' 내에 이미지 필드에서 지정한 경로(upload_to)로 저장된다.



**upload.html(templates)**

```html
<form action="" method="post" enctype="mulipart/form-data">
    <div class="alert alert-info">Please enter your photo information.</div>
    {% csrf_token %}
    {{form.as_p}}
    <input type="submit" value="Upload" class="btn btn-outline-primary">
</form>
```

- enctype : 파일 전송 시, 어떤 형태로 인코딩해서 서버로 전달하는지 결정(MIME(Multipurpose Internet Mail Extensions) : type/subtype 구조)
  - application/* : 기본 옵션. 모든 문자열을 인코딩해 전달하며 특수 문자는 ASCII HEX값으로 변환하고 띄어쓰기는 '+'로 변환하여 전달한다.
  - multipart/* : 파일 업로드 때 사용하는 옵션. 데이터를 문자열로 인코딩하지 않고 전달한다.
  - text/* : 띄어쓰기만 '+'로 변환하고 특별한 인코딩 없이 문자로 전달한다.

[HTML MIME 구조](https://developer.mozilla.org/ko/docs/Web/HTTP/Basics_of_HTTP/MIME_types)[(전체 구조)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Complete_list_of_MIME_types) : 클라이언트에게 전송된 문서의 다양성(타입)을 알려주기 위한 메커니즘

| main-type                                                    |                                     | sub-type                                                     |
| ------------------------------------------------------------ | ----------------------------------- | ------------------------------------------------------------ |
| **text**                                                     | text로 구성된 문서 파일             | text/plain<br />text/html<br />text/css<br />text/javascript<br />... |
| **image**                                                    | 이미지 파일                         | image/gif<br />image/png<br />image/jpeg<br />image/bmp<br />image/webp<br />... |
| **audio**                                                    | 오디오 파일                         | audio/midi<br />audio/mpeg<br />audio/webm<br />audio/ogg<br />audio/wav<br />... |
| **video**                                                    | 비디오 파일                         | video/webm<br />video/ogg<br />…                             |
| **application**                                              | 이진 데이터                         | application/octet-stream<br />application/pkcs12<br />application/vnd.mspowerpoint<br />application/xhtml+xml<br />application/xml<br />application/pdf<br />... |
| [multipart](https://developer.mozilla.org/ko/docs/Web/HTTP/Basics_of_HTTP/MIME_types#%EB%A9%80%ED%8B%B0%ED%8C%8C%ED%8A%B8_%ED%83%80%EC%9E%85) | 다른 MIME 타입을 지닌 문서 카테고리 | [form-data](https://developer.mozilla.org/ko/docs/Web/HTTP/Basics_of_HTTP/MIME_types#multipartform-data)<br />byteranges<br />... |

