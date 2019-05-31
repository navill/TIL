# View

- django의 ```view```는 요청(request)과 응답(response)에 대한 처리를 함수형 뷰 또는 제네릭 뷰로 구현한다.

- Generic view - CRUDL

  | Type   | Class      | Description                                                  |
  | ------ | ---------- | ------------------------------------------------------------ |
  | List   | ListView   | This renders any iterable of items, such as a `queryset`.    |
  | Edit   | CreateView | This renders and processes a form for `creating` new objects. |
  | Edit   | UpdateView | This renders and processes a form for `updating` an object.  |
  | Edit   | DeleteView | This renders and processes a form for `deleting` an object.  |
  | Detail | DetailView | This renders an item based on `pk` or `slug` from `URLConf`. |

> [Classy Class-Based Views.]([http://ccbv.co.uk/](http://ccbv.co.uk/)) : reference of generic view
>
> [Django Vanilla Views](http://django-vanilla-views.org/) :  사용자 정의 클래스는 유연한 기능 구현이 가능하지만 협업 시 다른 개발자들은 이해하기 어려울 수 있으므로 상황에 따라 third-party library를 사용하는 것이 좋을 수 있다.



### Mixin

