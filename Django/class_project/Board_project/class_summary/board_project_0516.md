# Board_Project_0516

- 댓글 기능 추가(Todo: ajax를 이용해 페이지 리로딩 제거)

board_detail.html : 글 + 댓글

Todo => board_detail.html : 글 + board_comment.html : 댓글





```
update & delete
페이지에 접근했을 때 구동되는 로직
함수형
1. 해당 객체 있는지 확인 - get_object_or_404, object.get, objects.filter.exists
2. 객체에 대한 권한 체크 - 작성자 또는 관리자
3-1. get -> 해당 페이지에 필요한 값 입력 받기
3-2. post -> 입력 받은 값에 대한 처리(삭제, 업데이트)
4. 처리 후 페이지 이동

클래스뷰
1. 객체에 대한 권한 체크 - 작성자 또는 관리자(dispatch)
def dispatch(self, request, *args, **kwargs):
  object = self.get_object()
# 권한체크.1
  super().dispatch(request, *args, **kwargs)
# 권한체크.2
  if request.method == "POST":
      super().post(request, *args, **kwargs)
  else:
      super().get(request, *args, **kwargs)
2. 해당 객체 있는지 확인 - get_object_or_404, object.get, objects.filter.exists(get_object, get_queryset)
3-1. get -> 해당 페이지에 필요한 값 입력 받기 (def get())
3-2. post -> 입력 받은 값에 대한 처리(삭제, 업데이트)(def post())
4. 처리 후 페이지 이동
```





### Todo

1. 영화 모델

2. 사용자는 영화를 선택하고 리뷰를 남긴다.

   2-1. 평점, 관람평, 좋아요, 싫어요

   평점 -> Choice field(1~5)

   2-2. 별 선택하기(javascript)

3. Mypage에서 내가 남긴 리뷰 모아보기 - 영화 목록 & 리뷰 목록

4. 