import argparse
import io
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

try:
    import psutil
except ImportError:
    print("psutil이 설치되어 있지 않습니다.")
    print("설치 방법: pip install psutil")
    sys.exit(1)


# ANSI 색상 및 커서 제어 코드
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    MAGENTA = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

    # 커서 제어
    CURSOR_HOME = '\033[H'  # 커서를 화면 맨 위로 이동
    CLEAR_LINE = '\033[K'  # 현재 줄 지우기
    CLEAR_SCREEN = '\033[2J'  # 화면 전체 지우기
    HIDE_CURSOR = '\033[?25l'  # 커서 숨기기
    SHOW_CURSOR = '\033[?25h'  # 커서 보이기


class ScreenBuffer:
    """더블 버퍼링을 위한 화면 버퍼 클래스"""

    def __init__(self, no_color: bool = False):
        self.buffer = io.StringIO()
        self.no_color = no_color
        self._last_line_count = 0

    def write(self, text: str = "") -> None:
        """버퍼에 텍스트 쓰기"""
        self.buffer.write(text + "\n")

    def flush_to_screen(self) -> None:
        """버퍼 내용을 화면에 출력 (깜빡임 없이)"""
        content = self.buffer.getvalue()
        lines = content.split('\n')
        current_line_count = len(lines)

        # 커서를 화면 맨 위로 이동
        sys.stdout.write(Colors.CURSOR_HOME)

        # 각 줄을 출력하고 나머지 부분 지우기
        for line in lines:
            sys.stdout.write(line + Colors.CLEAR_LINE + '\n')

        # 이전 출력보다 줄 수가 적으면 남은 줄들 지우기
        if current_line_count < self._last_line_count:
            for _ in range(self._last_line_count - current_line_count):
                sys.stdout.write(Colors.CLEAR_LINE + '\n')

        sys.stdout.flush()
        self._last_line_count = current_line_count

        # 버퍼 초기화
        self.buffer = io.StringIO()

    def clear(self) -> None:
        """버퍼 초기화"""
        self.buffer = io.StringIO()


# 백엔드 서비스 타입 정의
class ServiceType:
    DAPHNE = 'daphne'
    GUNICORN = 'gunicorn'
    UVICORN = 'uvicorn'
    DJANGO_DEV = 'django'
    FASTAPI_DEV = 'fastapi'
    HYPERCORN = 'hypercorn'
    AUTO = 'auto'
    ALL = 'all'


# 서비스 타입별 프로세스 감지 패턴
SERVICE_PATTERNS = {
    ServiceType.DAPHNE: ['daphne', 'config.asgi', 'asgi.py'],
    ServiceType.GUNICORN: ['gunicorn'],
    ServiceType.UVICORN: ['uvicorn'],
    ServiceType.DJANGO_DEV: ['manage.py runserver', 'django'],
    ServiceType.FASTAPI_DEV: ['fastapi dev', 'fastapi run'],
    ServiceType.HYPERCORN: ['hypercorn'],
}


def find_processes_by_service(
        service_type: str,
        port: Optional[int] = None,
        process_name: Optional[str] = None
) -> List[psutil.Process]:
    """
    서비스 타입, 포트, 프로세스명으로 백엔드 프로세스 찾기

    Args:
        service_type: 서비스 타입 (daphne, gunicorn, etc.)
        port: 필터링할 포트 번호
        process_name: 사용자 정의 프로세스명

    Returns:
        찾은 프로세스 리스트
    """
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()

            # 사용자 정의 프로세스명 우선
            if process_name and process_name.lower() in cmdline:
                processes.append(proc)
                continue

            # 서비스 타입별 패턴 매칭
            if service_type in [ServiceType.AUTO, ServiceType.ALL]:
                # 모든 패턴 확인
                for patterns in SERVICE_PATTERNS.values():
                    if any(pattern in cmdline for pattern in patterns):
                        processes.append(proc)
                        break
            elif service_type in SERVICE_PATTERNS:
                patterns = SERVICE_PATTERNS[service_type]
                if any(pattern in cmdline for pattern in patterns):
                    processes.append(proc)

            # 포트 필터링
            if port and processes and processes[-1] == proc:
                has_port = False
                try:
                    for conn in proc.connections(kind='tcp'):
                        if conn.laddr and conn.laddr.port == port:
                            has_port = True
                            break
                    if not has_port:
                        processes.pop()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    processes.pop()

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return processes


def detect_service_type(proc: psutil.Process) -> str:
    """프로세스에서 서비스 타입 감지"""
    try:
        cmdline = ' '.join(proc.cmdline() or []).lower()

        for service, patterns in SERVICE_PATTERNS.items():
            if any(pattern in cmdline for pattern in patterns):
                return service

        return 'unknown'
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 'unknown'


def is_master_process(proc: psutil.Process, all_procs: List[psutil.Process]) -> bool:
    """마스터 프로세스 여부 확인 (자식 프로세스가 있는지)"""
    try:
        pid = proc.pid
        for other in all_procs:
            try:
                if other.ppid() == pid:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def get_worker_processes(master_proc: psutil.Process, all_procs: List[psutil.Process]) -> List[psutil.Process]:
    """마스터 프로세스의 워커 프로세스들 찾기"""
    workers = []
    try:
        master_pid = master_proc.pid
        for proc in all_procs:
            try:
                if proc.ppid() == master_pid:
                    workers.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return workers


def format_bytes(bytes_value: int) -> str:
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"


def get_connection_state_color(state: str, no_color: bool = False) -> str:
    """연결 상태에 따른 색상 반환"""
    if no_color:
        return ''

    state_colors = {
        'ESTABLISHED': Colors.GREEN,
        'LISTEN': Colors.BLUE,
        'CLOSE_WAIT': Colors.YELLOW,
        'TIME_WAIT': Colors.YELLOW,
        'SYN_SENT': Colors.CYAN,
        'SYN_RECV': Colors.CYAN,
    }
    return state_colors.get(state, Colors.NC)


def display_process_info(proc: psutil.Process, buf: ScreenBuffer, is_master: bool = False,
                         no_color: bool = False) -> None:
    """프로세스 정보 출력"""
    try:
        with proc.oneshot():
            pid = proc.pid
            username = proc.username()
            cpu_percent = proc.cpu_percent(interval=0.1)
            mem_info = proc.memory_info()
            mem_percent = proc.memory_percent()
            create_time = datetime.fromtimestamp(proc.create_time()).strftime('%H:%M:%S')
            service_type = detect_service_type(proc)

            role = f"[{'MASTER' if is_master else 'WORKER'}]" if not no_color else f"[{'M' if is_master else 'W'}]"
            role_color = Colors.MAGENTA if is_master else Colors.CYAN

            if no_color:
                buf.write(f"프로세스 정보 {role}:")
                buf.write(f"  PID: {pid} | Type: {service_type} | User: {username} | "
                          f"CPU: {cpu_percent:.1f}% | MEM: {mem_percent:.1f}% ({format_bytes(mem_info.rss)}) | "
                          f"Start: {create_time}")
            else:
                buf.write(f"{Colors.CYAN}프로세스 정보 {role_color}{role}{Colors.NC}:")
                buf.write(f"  PID: {pid} | Type: {Colors.YELLOW}{service_type}{Colors.NC} | User: {username} | "
                          f"CPU: {cpu_percent:.1f}% | MEM: {mem_percent:.1f}% ({format_bytes(mem_info.rss)}) | "
                          f"Start: {create_time}")
            buf.write()
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        if no_color:
            buf.write(f"프로세스 정보를 가져올 수 없습니다: {e}")
        else:
            buf.write(f"{Colors.RED}프로세스 정보를 가져올 수 없습니다: {e}{Colors.NC}")


def get_connections_via_lsof(pid: int) -> List[Dict]:
    """lsof 명령어를 사용하여 TCP 연결 정보 가져오기 (macOS용 fallback)"""
    import subprocess

    connections = []
    try:
        result = subprocess.run(
            ['lsof', '-i', 'TCP', '-a', '-p', str(pid), '-n', '-P'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return connections

        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:  # 헤더만 있는 경우
            return connections

        for line in lines[1:]:  # 헤더 스킵
            parts = line.split()
            if len(parts) >= 9:
                # lsof 출력 파싱: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
                fd_str = parts[3]
                name = parts[8] if len(parts) >= 9 else parts[-1]
                state = parts[9] if len(parts) >= 10 else ''

                # 상태 파싱 (괄호 안의 상태)
                status = 'UNKNOWN'
                if '(LISTEN)' in line:
                    status = 'LISTEN'
                elif '(ESTABLISHED)' in line:
                    status = 'ESTABLISHED'
                elif '(CLOSE_WAIT)' in line:
                    status = 'CLOSE_WAIT'
                elif '(TIME_WAIT)' in line:
                    status = 'TIME_WAIT'
                elif '(SYN_SENT)' in line:
                    status = 'SYN_SENT'
                elif '(SYN_RECV)' in line:
                    status = 'SYN_RECV'

                # 주소 파싱
                laddr = '-'
                raddr = '-'

                if '->' in name:
                    # 연결된 상태: local->remote
                    addr_parts = name.split('->')
                    laddr = addr_parts[0]
                    raddr = addr_parts[1] if len(addr_parts) > 1 else '-'
                else:
                    # LISTEN 상태 등
                    laddr = name

                # FD 번호 추출 (예: "5u" -> 5)
                fd = -1
                if fd_str and fd_str[:-1].isdigit():
                    fd = int(fd_str[:-1])

                connections.append({
                    'fd': fd,
                    'laddr': laddr,
                    'raddr': raddr,
                    'status': status
                })

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return connections


def display_connections(proc: psutil.Process, buf: ScreenBuffer, no_color: bool = False) -> Optional[Dict]:
    """TCP 연결 정보 출력"""
    pid = proc.pid
    use_lsof = False
    connections = get_connections_via_lsof(pid)

    if not connections:
        if no_color:
            buf.write("  활성 연결 없음")
        else:
            buf.write(f"  {Colors.YELLOW}활성 연결 없음{Colors.NC}")
        return {
            'total': 0,
            'established': 0,
            'listen': 0,
            'close_wait': 0,
            'time_wait': 0,
            'remote_ips': defaultdict(int)
        }

    # 헤더 출력
    if no_color:
        buf.write(f"{'TYPE':<10} {'FD':<8} {'LOCAL':<25} {'REMOTE':<25} {'STATE':<12}")
    else:
        buf.write(f"{Colors.BOLD}{'TYPE':<10} {'FD':<8} {'LOCAL':<25} {'REMOTE':<25} {'STATE':<12}{Colors.NC}")
    buf.write("  " + "-" * 89)

    stats = {
        'total': len(connections),
        'established': 0,
        'listen': 0,
        'close_wait': 0,
        'time_wait': 0,
        'remote_ips': defaultdict(int)
    }

    for conn in connections:
        if use_lsof:
            # lsof 결과 (dict)
            fd = conn['fd']
            laddr = conn['laddr']
            raddr = conn['raddr']
            status = conn['status']

            # 원격 IP 추출 (예: "192.168.1.1:8080" -> "192.168.1.1")
            remote_ip = None
            if raddr and raddr != '-' and ':' in raddr:
                remote_ip = raddr.rsplit(':', 1)[0]
        else:
            # psutil 결과
            fd = conn.fd
            laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
            raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
            status = conn.status
            remote_ip = conn.raddr.ip if conn.raddr else None

        # 통계 수집
        if status == 'ESTABLISHED':
            stats['established'] += 1
            if remote_ip:
                stats['remote_ips'][remote_ip] += 1
        elif status == 'LISTEN':
            stats['listen'] += 1
        elif status == 'CLOSE_WAIT':
            stats['close_wait'] += 1
        elif status == 'TIME_WAIT':
            stats['time_wait'] += 1

        # 색상 적용
        state_color = get_connection_state_color(status, no_color)
        nc = '' if no_color else Colors.NC

        buf.write(f"  {'TCP':<10} {fd:<8} {laddr:<25} {raddr:<25} "
                  f"{state_color}{status:<12}{nc}")

    return stats


def display_stats(stats: Dict, buf: ScreenBuffer, service_type: str, no_color: bool = False) -> None:
    """연결 통계 출력"""
    if not stats:
        return

    if no_color:
        buf.write("\n연결 통계:")
        buf.write(f"  전체: {stats['total']} | "
                  f"ESTABLISHED: {stats['established']} | "
                  f"LISTEN: {stats['listen']} | "
                  f"CLOSE_WAIT: {stats['close_wait']} | "
                  f"TIME_WAIT: {stats['time_wait']}")
    else:
        buf.write(f"\n{Colors.CYAN}연결 통계:{Colors.NC}")
        buf.write(f"  전체: {Colors.BOLD}{stats['total']}{Colors.NC} | "
                  f"ESTABLISHED: {Colors.GREEN}{stats['established']}{Colors.NC} | "
                  f"LISTEN: {Colors.BLUE}{stats['listen']}{Colors.NC} | "
                  f"CLOSE_WAIT: {Colors.YELLOW}{stats['close_wait']}{Colors.NC} | "
                  f"TIME_WAIT: {Colors.YELLOW}{stats['time_wait']}{Colors.NC}")

    # 활성 연결 정보
    service_display = {
        ServiceType.DAPHNE: "WebSocket/ASGI",
        ServiceType.GUNICORN: "WSGI",
        ServiceType.UVICORN: "ASGI",
        ServiceType.DJANGO_DEV: "Django Dev",
        ServiceType.FASTAPI_DEV: "FastAPI Dev",
        ServiceType.HYPERCORN: "ASGI",
    }.get(service_type, "Backend")

    if no_color:
        buf.write(f"\n{service_display} 활성 연결:")
        if stats['established'] > 0:
            buf.write(f"  활성 연결: {stats['established']}개")
        else:
            buf.write(f"  활성 연결 없음")
    else:
        buf.write(f"\n{Colors.CYAN}{service_display} 활성 연결:{Colors.NC}")
        if stats['established'] > 0:
            buf.write(f"  활성 연결: {Colors.GREEN}{stats['established']}{Colors.NC}개")
        else:
            buf.write(f"  {Colors.YELLOW}활성 연결 없음{Colors.NC}")

    # 원격 IP 통계
    if stats['remote_ips']:
        if no_color:
            buf.write("\n원격 클라이언트 IP:")
        else:
            buf.write(f"\n{Colors.CYAN}원격 클라이언트 IP:{Colors.NC}")

        sorted_ips = sorted(stats['remote_ips'].items(), key=lambda x: x[1], reverse=True)
        for ip, count in sorted_ips[:10]:  # 상위 10개만 표시
            if no_color:
                buf.write(f"  {ip}: {count} 연결")
            else:
                buf.write(f"  {ip}: {Colors.GREEN}{count}{Colors.NC} 연결")


def aggregate_stats(stats_list: List[Dict]) -> Dict:
    """여러 프로세스의 통계 집계"""
    aggregated = {
        'total': 0,
        'established': 0,
        'listen': 0,
        'close_wait': 0,
        'time_wait': 0,
        'remote_ips': defaultdict(int)
    }

    for stats in stats_list:
        if not stats:
            continue
        aggregated['total'] += stats['total']
        aggregated['established'] += stats['established']
        aggregated['listen'] += stats['listen']
        aggregated['close_wait'] += stats['close_wait']
        aggregated['time_wait'] += stats['time_wait']

        for ip, count in stats['remote_ips'].items():
            aggregated['remote_ips'][ip] += count

    return aggregated


def monitor_connections(
        service_type: str = ServiceType.AUTO,
        port: Optional[int] = None,
        process_name: Optional[str] = None,
        refresh_interval: int = 2,
        no_color: bool = False
) -> None:
    """메인 모니터링 루프 (더블 버퍼링으로 깜빡임 방지)"""
    buf = ScreenBuffer(no_color)

    try:
        # 커서 숨기기 및 초기 화면 클리어
        sys.stdout.write(Colors.HIDE_CURSOR)
        sys.stdout.write(Colors.CLEAR_SCREEN)
        sys.stdout.flush()

        while True:
            # 헤더
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if no_color:
                buf.write("=" * 50)
                buf.write("Backend Service Connection Monitor")
                buf.write("=" * 50)
                buf.write(f"갱신 시간: {current_time}")
                buf.write()
            else:
                buf.write(f"{Colors.BOLD}{Colors.CYAN}{'=' * 50}")
                buf.write("Backend Service Connection Monitor")
                buf.write(f"{'=' * 50}{Colors.NC}")
                buf.write(f"{Colors.YELLOW}갱신 시간: {current_time}{Colors.NC}")
                buf.write()

            # 프로세스 찾기
            processes = find_processes_by_service(service_type, port, process_name)

            if not processes:
                service_desc = process_name if process_name else service_type
                if no_color:
                    buf.write(f"{service_desc} 프로세스를 찾을 수 없습니다.")
                else:
                    buf.write(f"{Colors.RED}{service_desc} 프로세스를 찾을 수 없습니다.{Colors.NC}")

                if no_color:
                    buf.write(f"\n다음 갱신까지 {refresh_interval}초... (Ctrl+C로 종료)")
                else:
                    buf.write(f"\n{Colors.YELLOW}다음 갱신까지 {refresh_interval}초... (Ctrl+C로 종료){Colors.NC}")

                buf.flush_to_screen()
                time.sleep(refresh_interval)
                continue

            # 서비스 타입 감지
            detected_services = set(detect_service_type(p) for p in processes)
            service_str = ', '.join(detected_services)

            if no_color:
                buf.write(f"감지된 서비스: {service_str}")
                buf.write(f"프로세스 PID: {', '.join(str(p.pid) for p in processes)}")
                buf.write()
            else:
                buf.write(f"{Colors.GREEN}감지된 서비스: {service_str}{Colors.NC}")
                buf.write(f"{Colors.GREEN}프로세스 PID: {', '.join(str(p.pid) for p in processes)}{Colors.NC}")
                buf.write()

            # 마스터-워커 구조 파악
            master_procs = []
            worker_procs = []
            standalone_procs = []

            for proc in processes:
                if is_master_process(proc, processes):
                    master_procs.append(proc)
                elif proc.ppid() in [p.pid for p in processes]:
                    worker_procs.append(proc)
                else:
                    standalone_procs.append(proc)

            all_stats = []

            # 마스터 프로세스 출력
            for proc in master_procs:
                if no_color:
                    buf.write(f"[MASTER PID: {proc.pid}]")
                else:
                    buf.write(f"{Colors.BOLD}{Colors.MAGENTA}[MASTER PID: {proc.pid}]{Colors.NC}")

                display_process_info(proc, buf, is_master=True, no_color=no_color)

                if no_color:
                    buf.write("TCP 연결 상태:")
                else:
                    buf.write(f"{Colors.CYAN}TCP 연결 상태:{Colors.NC}")

                stats = display_connections(proc, buf, no_color)
                if stats:
                    all_stats.append(stats)
                    display_stats(stats, buf, detect_service_type(proc), no_color)

                # 워커 프로세스 출력
                workers = get_worker_processes(proc, processes)
                if workers:
                    buf.write("\n  " + "-" * 85)
                    if no_color:
                        buf.write(f"  워커 프로세스 ({len(workers)}개):")
                    else:
                        buf.write(f"  {Colors.CYAN}워커 프로세스 ({len(workers)}개):{Colors.NC}")
                    buf.write("  " + "-" * 85)
                    buf.write()

                    for worker in workers:
                        if no_color:
                            buf.write(f"  [WORKER PID: {worker.pid}]")
                        else:
                            buf.write(f"  {Colors.BOLD}{Colors.CYAN}[WORKER PID: {worker.pid}]{Colors.NC}")

                        display_process_info(worker, buf, is_master=False, no_color=no_color)

                        if no_color:
                            buf.write("  TCP 연결 상태:")
                        else:
                            buf.write(f"  {Colors.CYAN}TCP 연결 상태:{Colors.NC}")

                        worker_stats = display_connections(worker, buf, no_color)
                        if worker_stats:
                            all_stats.append(worker_stats)
                            display_stats(worker_stats, buf, detect_service_type(worker), no_color)
                        buf.write()

                buf.write("\n" + "-" * 89)
                buf.write()

            # 독립 프로세스 출력
            for proc in standalone_procs:
                if no_color:
                    buf.write(f"[PID: {proc.pid}]")
                else:
                    buf.write(f"{Colors.BOLD}{Colors.BLUE}[PID: {proc.pid}]{Colors.NC}")

                display_process_info(proc, buf, no_color=no_color)

                if no_color:
                    buf.write("TCP 연결 상태:")
                else:
                    buf.write(f"{Colors.CYAN}TCP 연결 상태:{Colors.NC}")

                stats = display_connections(proc, buf, no_color)
                if stats:
                    all_stats.append(stats)
                    display_stats(stats, buf, detect_service_type(proc), no_color)

                buf.write("\n" + "-" * 89)
                buf.write()

            # 전체 통계 (여러 프로세스가 있을 경우)
            if len(all_stats) > 1:
                aggregated = aggregate_stats(all_stats)
                if no_color:
                    buf.write("=" * 50)
                    buf.write("전체 통계 (모든 프로세스 합계)")
                    buf.write("=" * 50)
                else:
                    buf.write(f"{Colors.BOLD}{Colors.MAGENTA}{'=' * 50}")
                    buf.write("전체 통계 (모든 프로세스 합계)")
                    buf.write(f"{'=' * 50}{Colors.NC}")

                display_stats(aggregated, buf, service_type, no_color)
                buf.write("\n" + "=" * 89)
                buf.write()

            if no_color:
                buf.write(f"다음 갱신까지 {refresh_interval}초... (Ctrl+C로 종료)")
            else:
                buf.write(f"{Colors.YELLOW}다음 갱신까지 {refresh_interval}초... (Ctrl+C로 종료){Colors.NC}")

            # 버퍼 내용을 화면에 출력 (깜빡임 없이)
            buf.flush_to_screen()
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        pass
    finally:
        # 커서 다시 보이기
        sys.stdout.write(Colors.SHOW_CURSOR)
        sys.stdout.flush()
        if no_color:
            print("\n\n모니터링을 종료합니다.")
        else:
            print(f"\n\n{Colors.CYAN}모니터링을 종료합니다.{Colors.NC}")
        sys.exit(0)


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description='Generic Backend Service TCP Connection Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 자동 감지 모드 (모든 백엔드 서비스 탐색)
  %(prog)s

  # 특정 서비스 타입 모니터링
  %(prog)s -s daphne
  %(prog)s -s gunicorn
  %(prog)s -s uvicorn

  # 포트 기반 필터링
  %(prog)s -s daphne -p 8000

  # 사용자 정의 프로세스명
  %(prog)s -n "python manage.py"

  # 갱신 주기 설정 (기본 2초)
  %(prog)s -s gunicorn -i 5

  # 색상 없이 출력
  %(prog)s --no-color

지원 서비스:
  - Daphne (Django Channels ASGI)
  - Gunicorn (Django WSGI)
  - Uvicorn (FastAPI ASGI)
  - Django runserver (개발 서버)
  - FastAPI dev server
  - Hypercorn
        """
    )

    parser.add_argument(
        '-s', '--service',
        choices=[
            ServiceType.DAPHNE,
            ServiceType.GUNICORN,
            ServiceType.UVICORN,
            ServiceType.DJANGO_DEV,
            ServiceType.FASTAPI_DEV,
            ServiceType.HYPERCORN,
            ServiceType.ALL,
            ServiceType.AUTO
        ],
        default=ServiceType.AUTO,
        help='모니터링할 서비스 타입 (기본: auto)'
    )

    parser.add_argument(
        '-p', '--port',
        type=int,
        help='필터링할 포트 번호'
    )

    parser.add_argument(
        '-n', '--process-name',
        type=str,
        help='사용자 정의 프로세스명 패턴'
    )

    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=2,
        help='화면 갱신 주기 (초, 기본: 2)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='색상 출력 비활성화'
    )

    args = parser.parse_args()

    # 시작 메시지
    service_desc = args.process_name if args.process_name else args.service
    port_desc = f" (port: {args.port})" if args.port else ""

    if args.no_color:
        print(f"\n{service_desc} 서비스 모니터링 시작...{port_desc}\n")
    else:
        print(f"\n{Colors.CYAN}{service_desc} 서비스 모니터링 시작...{port_desc}{Colors.NC}\n")

    time.sleep(1)

    monitor_connections(
        service_type=args.service,
        port=args.port,
        process_name=args.process_name,
        refresh_interval=args.interval,
        no_color=args.no_color
    )


if __name__ == "__main__":
    main()
