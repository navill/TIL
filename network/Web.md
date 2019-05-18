# Web

- HTTP(HyperText Transfer Protocol) : 요청과 응답을 교환하기 위한 클라이언트와 웹 서버의 명세
- HTML(HyperText Markup Language) : 요청 결과에 대한 표현 형식
- URL(Uniform Resource Locator) : 고유의 해당 서버와 자원을 나타내는 방법
  - Client(web browser)는 HTTP로 URL을 요청하고 Server로 부터 HTML을 받는다.

------

- Connectionless : 서버는 클라이언트의 요청에 대한 응답을 송신하고 정상적인 통신이 완료될 경우 통신은 종료.
  -> 헤더의 keep-alive를 통해 커넥션을 유지할 수 있다(HTTP 1.1).
- Stateless : 통신이 완료될 경우 상태 초기화.
  -> 이때 발생하는 문제(단점)를 극복하기 위해 다음과 같은 기술을 사용할 수 있다.
  - Caching : 첫 요청-응답이 완료되었을 때 정적인 원격 콘텐츠는 클라이언트에 저장, 이후 서버로부터 동일한 콘텐츠를 다운로드 하지않고 저장된 콘텐츠를 사용한다.
  - Session : 서버에서 클라이언트에게 제공하는 세션ID를 통해 클라이언트 식별한다.
    - 브라우저가 종료될 때 까지 인증상태 유지(인증상태 유지 시간은 설정할 수 있음)
    - 사용자 정보 파일을 서버측에서 관리
    - 사용자 수만큼 서버에 부하가 걸리기 때문에 JWT(JSON Web Token) 방식으로 단점을 보완
  - Authentication : 사용자를 식별하기 위해 식별값(아이디, 비밀번호)을 기억하고 이를 이용할 수 있다.
  - Cookie : 서버가 클라이언트를 식별 할 수 있도록 클라이언트에 보내는 정보. 클라이언트는 서버에 다시 쿠키를 보냄으로써 서버는 클라이언트를 식별할 수 있게 된다.

------

# web framework

- Web framework : 웹 사이트를 구축할 수 있는 기능 제공
- Web framework는 다음 기능을 포함한다.
  1. Route : URL을 해석하여 해당 서버의 파일이나 파이썬 코드를 검색
  2. Template : 서버 사이드의 데이터를 HTML 페이지에 병합
  3. Authentication and authorization : 사용자 이름과 비밀번호, 허가 등을 처리한다.
  4. Session : 웹 사이트에 방문하는 동안 사용자의 임시 데이터를 유지한다.

------

# Web Application Server





