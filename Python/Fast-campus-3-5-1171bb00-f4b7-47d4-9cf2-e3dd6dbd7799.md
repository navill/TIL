# Fast campus(3/5)

Created: Mar 05, 2019 2:05 PM

- Tags: bubble sort,data structure,dictionary,namespace

# <프로그래머가 갖춰야 할 기술>
- Recursion, index, sort, Binary search → 자료구조, 알고리즘
- Stack, Heap(memory) → 메모리(layout)에 대한 이해
- Process & Thread → OS에 대한 이해, multi-thread → thread pool
- Call by Value/Call by Reference → 함수 (python : call by object reference)
- M(model)V(view)C(controller) Architecture → design pattern
- Write simple text-based games
---



**자료 구조 세가지 개념(+ getRandom)**

[Design a data structure that supports insert, delete, search and getRandom in constant time - GeeksforGeeks](https://www.geeksforgeeks.org/design-a-data-structure-that-supports-insert-delete-search-and-getrandom-in-constant-time/)


Design a data structure that supports following operations in Θ(1) time.

insert(x): Inserts an item x to the data structure if not already present.

remove(x): Removes an item x from the data structure if present.

search(x): Searches an item x in the data structure.

getRandom(): Returns a random element from current set of elements

---

## Dictionary를 구현하기 위해 사용되는 기술

1. BTS(binary-tree search)
2. Hash table
    - Python의 list는 메모리가 c언어 배열 처럼 붙어있지 않다 → c 언어에 비해 memory에 대한 취약점이 있다
    - Dictionary : key와 value를 한쌍으로 하는 자료 구조
    - immutable object : 변하지 않는 자료구조 -> tuple(hashable type), 문자열 등...



---

### dic.get('key', (option) default value)
-> 없는 키값 사용 시 dic['a'] vs dic.get('a')의 결정적인 차이: 에러의 유무

    # dic['e'] - example
    >>> dic['e']
    KeyError                                  Traceback (most recent call last)
    <ipython-input-23-87d22c709971> in <module>
    ----> 1 dic['e']
    KeyError: 'e'
    	# KeyError를 일으킨다
    --------------------------------
    # dic.get('e') - example
    >>> dic.get('e')
    --------------------------------
    'None'
    	# None을 반환한다

### dic.setdefault('e', 10)
→ 'e'라는 키 값이 없을 경우 두 번째 인자를 default 값으로 사용

# 

## insert - update()

### 매개 변수가 tuple type이더라도 dictionary에 update 사용할 수 있다.
    c=(('a', 3), ('b', 4))
    dic.update(c)


#

## view - keys(), values(), items()

### key_list = list(dic.keys()) → 값이 수정(dic.update) 되더라도 원본 값(key_list)에 영향을 주지 않는다

* 가변 객체인 하나의 새로운 리스트를 생성하기 때문에 dic과 key_list는 전혀 다른 객체가 된다.

### key_view = dic.keys() → 값이 수정 될 경우 원본 값에 영향을 준다

* dict.keys(), dict.values() 그리고 dict.items()에 의해 반환되는 객체를 view objects라 한다
* View objects provide a dynamic view on the dictionary’s entries

    
    
    dic = {'a': 1, 'b': 2}
    
    
    key_list = list(dic.keys())
    key_view = dic.keys()
    
    print(key_list)  #  ['a', 'b']
    print(key_view)  #  dict_keys(['a', 'b'])
    
    dic.__setitem__('c', 3)
    print(key_list)  #  ['a', 'b']
    print(key_view)  #  dict_keys(['a', 'b', 'c'])




# 파이썬에서 False로 간주하는 객체

- False
- None
- "", ''
- []
- {}
- ()

---

# <논리 연산자 → True or False를 결정하는 값을 반환>

    # a and b  
    a가 거짓이면 b와 상관없이 거짓이므로 a를 반환하고, a가 참이면 b에 의해 참 혹은 거짓이 결정되므로 
    b를 반환합니다.
    
    # a or b 
    a가 거짓이면 b에 의해 참 혹은 거짓이 결정되므로 b를 반환하고, a가 참이면 b와 상관없이 참이므로 
    a를 반환합니다.

# Namespace

- 특정 이름이 유일하고, 다른 네임 스페이스에서의 같은 이름을 가진 변수와 관계가 없는 것을 의미한다.
    - local namespace의 변수(local variable)는 함수 실행 후 메모리에서 사라짐

```
# Namespace
a = 10  # global - a
def outer():
    # Local Namespace
    global a  # 전역변수 a에 접근(&수정)하기 위해 변수 앞에 global 사용
    b = 20  # outer 안의 지역변수 - b
    print('outer.b:', b, 'id:', id(b))

    def inner1():
        b = 30  # inner1 안의 지역변수 - b
        print('inner1.b:', b, 'id-:', id(b))
        def inner2():
            nonlocal b  # 지역변수도, 전역변수도 아닌 변수 - b
            # nonlocal이 아닌 b를 할당할 경우 접근은 가능하지만 수정(inner2() 내부에서)
            # 할 수 없다(inner1()의 b와 연결이 끊어지고 새로운 inner2()의 지역변수 b가 생성된다.)
            # print('type-:', id(b))
            b = 40  # inner2 안의 지역변수 - d
            print('inner2.b:', b, 'id:', id(b))
        inner2()
        print('from inner1.b:', b, 'id:', id(b))  # if nonlocal: 40, else: 30
        # inner2의 변수 b가 nonlocal 일 때, inner1의 b와 바인딩 된다 - inner2.b == inner1.b
        # inner2의 변수 b가 local 일 때, inner1과는 별개의 객체가 된다 - inner2.b != inner1.b
    inner1()
outer()

# Output : 30
```
---

# li.sort()와 sorted(li)는 short sort로 구현된다

→ list.sort()와 sorted(list)의 차이

    li1 = [1, 5, 3, 4, 5]
    li2 = [1, 5, 3, 4, 5]
    a = li1.sort()  # list.sort() -> none
    # list 객체를 직접 수정하고 none을 반환한다
    # 주로 객체를 수정하고 수정된 객체로부터 반환할 것이 없다는 뜻으로 none을 반환한다
    b = sorted(li2)  # sorted() -> ordered new list object
    # 정렬된 새로운 리스트 객체를 반환한다

---

# Dictionary view objects

- **`Dictionary views can be iterated`** over to yield their respective data
- They provide a **`dynamic view on the dictionary’s entries`**, which means that when the dictionary changes, the view reflects these changes.

---

# Bubble sort

→ 효율이 매우 낮기 때문에 사용하지 않는다

    li = [5, 2, 9, 3, 8, 4]
    
    
    def bubble_sort(list_value):
        n = len(list_value)
        for i in range(n - 1):
            for j in range(n - i - 1):
                if list_value[j] > list_value[j + 1]:
                    list_value[j], list_value[j + 1] = list_value[j + 1], list_value[j]
    
        print(list_value)
    
    
    bubble_sort(li)
    
    # output : 
    # [2, 3, 4, 5, 8, 9]