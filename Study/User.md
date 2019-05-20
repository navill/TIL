## User

#### [User Fields](https://docs.djangoproject.com/ko/2.2/ref/contrib/auth/)

```from django.contrib.auth.models import User```

```author = models.ForeignKey(User, ...)```

- username, password, first & last_name 등 간단한 사용자 관련 간단한 fields 제공
- django에서 제공하는 기본 class

## AUTH_USER_MODEL

```from django.conf import settings```

```author = models.ForeignKey(settings.AUTH_USER_MODEL, ...)```

- app('users')의 models.py에 CustomModel class를 생성한 후, 이를 settings.py에 ```AUTH_USER_MODEL='users.CustomModel'``` 설정 함으로써 기본적인 구조는 완성된다.
- app마다 사용자 정보를 저장할 필요가 있을 경우 ```ForeignKey``` 또는 ```OneToOneField``` 를 ```settings.AUTH_USER_MODEL``` 로 사용해야한다.

## get_user_model

```from django.contrib.auth import get_user_model```

```author = models.ForeignKey(get_user_model, ...)```

- AUTH_USER_MODEL과 구조는 동일하나 import 시 settings가 아닌 get_user_model을 사용한다.

  


> 위 세 가지는 User 객체를 생성하기 위해 사용되는 기본적인 방법이다. django documents에 구체적으로 이 세 가지의 방식에 대해 명시하지 않고 있지만, 추후에 프로젝트 및 스터디를 진행하면서 차이를 확인하고 정리할 예정이다. (2019/5/14)

