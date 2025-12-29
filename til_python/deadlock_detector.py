import argparse
import hashlib
import re
import subprocess
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

"""
데드락 감지 스크립트

py-spy dump를 주기적으로 실행하여 스택 트레이스를 비교하고
데드락 상태를 감지합니다.

사용법:
    python scripts/deadlock_detector.py <pid>
    python scripts/deadlock_detector.py <pid> --interval 3 --threshold 3
    python scripts/deadlock_detector.py <pid> --watch  # 연속 모니터링 모드

요구사항:
    pip install py-spy

주의:
    py-spy는 root 권한이 필요할 수 있습니다.
    macOS: sudo 필요
    Linux: sudo 또는 CAP_SYS_PTRACE 권한 필요
"""


@dataclass
class ThreadSnapshot:
    """스레드 스냅샷"""
    thread_id: str
    thread_name: str
    stack_frames: list[str] = field(default_factory=list)

    @property
    def stack_hash(self) -> str:
        """스택 트레이스의 해시값"""
        stack_str = "\n".join(self.stack_frames)
        return hashlib.md5(stack_str.encode()).hexdigest()[:8]

    @property
    def top_frame(self) -> str:
        """최상위 프레임"""
        return self.stack_frames[0] if self.stack_frames else "unknown"

    def is_blocked(self) -> bool:
        """블로킹 상태 여부 판단"""
        blocking_patterns = [
            r"acquire",
            r"_wait",
            r"wait_for",
            r"\.get\(",
            r"\.put\(",
            r"lock\.",
            r"Queue\.",
            r"Event\.wait",
            r"Condition\.wait",
            r"Semaphore\.acquire",
        ]

        for frame in self.stack_frames[:5]:  # 상위 5개 프레임만 검사
            for pattern in blocking_patterns:
                if re.search(pattern, frame, re.IGNORECASE):
                    return True
        return False


@dataclass
class ProcessSnapshot:
    """프로세스 전체 스냅샷"""
    timestamp: datetime
    threads: list[ThreadSnapshot] = field(default_factory=list)
    raw_output: str = ""

    @property
    def thread_count(self) -> int:
        return len(self.threads)

    def get_blocked_threads(self) -> list[ThreadSnapshot]:
        """블로킹된 스레드 목록"""
        return [t for t in self.threads if t.is_blocked()]


class DeadlockDetector:
    """데드락 감지기"""

    def __init__(
            self,
            pid: int,
            interval: float = 5.0,
            threshold: int = 3,
            verbose: bool = False
    ):
        self.pid = pid
        self.interval = interval
        self.threshold = threshold  # 연속 동일 스택 횟수 임계값
        self.verbose = verbose

        # 메모리 효율: 스냅샷 객체 대신 카운터만 유지
        self.snapshot_count: int = 0
        # 메모리 효율: 최근 threshold 개의 해시만 유지 (deque)
        self.stack_history: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=threshold)
        )

    def run_py_spy_dump(self) -> Optional[str]:
        """py-spy dump 실행"""
        try:
            result = subprocess.run(
                ["py-spy", "dump", "--pid", str(self.pid)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"[오류] py-spy 실행 실패: {result.stderr}", file=sys.stderr)
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            print("[오류] py-spy 타임아웃", file=sys.stderr)
            return None
        except FileNotFoundError:
            print("[오류] py-spy가 설치되지 않았습니다. pip install py-spy", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print("[오류] 권한이 부족합니다. sudo로 실행하세요.", file=sys.stderr)
            sys.exit(1)

    def parse_dump(self, raw_output: str) -> ProcessSnapshot:
        """py-spy dump 출력 파싱"""
        snapshot = ProcessSnapshot(
            timestamp=datetime.now(),
            raw_output=raw_output
        )

        current_thread: Optional[ThreadSnapshot] = None

        for line in raw_output.split("\n"):
            # 스레드 헤더 파싱
            # 예: Thread 0x7f8b8c0 (active): "MainThread"
            thread_match = re.match(
                r'Thread\s+(0x[0-9a-fA-F]+|[\d]+)\s+\([^)]+\)(?::\s+"([^"]*)")?',
                line
            )

            if thread_match:
                if current_thread:
                    snapshot.threads.append(current_thread)

                thread_id = thread_match.group(1)
                thread_name = thread_match.group(2) or f"Thread-{thread_id}"
                current_thread = ThreadSnapshot(
                    thread_id=thread_id,
                    thread_name=thread_name
                )

            # 스택 프레임 파싱
            # 예:     function_name (filename.py:123)
            elif current_thread and line.strip():
                frame_match = re.match(r'\s+(.+\s+\(.+:\d+\))', line)
                if frame_match:
                    current_thread.stack_frames.append(frame_match.group(1).strip())

        # 마지막 스레드 추가
        if current_thread:
            snapshot.threads.append(current_thread)

        return snapshot

    def detect_deadlock(self, snapshot: ProcessSnapshot) -> dict:
        """데드락 감지"""
        result = {
            "is_deadlock": False,
            "suspected_threads": [],
            "confidence": 0.0,
            "details": []
        }

        # 각 스레드의 스택 해시를 히스토리에 추가
        for thread in snapshot.threads:
            self.stack_history[thread.thread_id].append(thread.stack_hash)

            # 최근 threshold 개의 해시가 모두 동일하면 데드락 의심
            # deque(maxlen=threshold)이므로 전체가 곧 최근 N개
            history = self.stack_history[thread.thread_id]
            if len(history) >= self.threshold:
                # deque는 슬라이싱 미지원 → 전체 사용 (maxlen으로 이미 제한됨)
                if len(set(history)) == 1 and thread.is_blocked():
                    result["suspected_threads"].append({
                        "thread_id": thread.thread_id,
                        "thread_name": thread.thread_name,
                        "top_frame": thread.top_frame,
                        "stack_hash": thread.stack_hash,
                        "blocked_count": self.threshold
                    })

        # 2개 이상의 스레드가 데드락 의심 상태면 데드락으로 판단
        if len(result["suspected_threads"]) >= 2:
            result["is_deadlock"] = True
            result["confidence"] = min(1.0, len(result["suspected_threads"]) / 4)
            result["details"].append(
                f"{len(result['suspected_threads'])}개 스레드가 "
                f"{self.threshold}회 연속 동일한 위치에서 블로킹됨"
            )

        return result

    def print_snapshot(self, snapshot: ProcessSnapshot) -> None:
        """스냅샷 출력"""
        print(f"\n{'=' * 60}")
        print(f"[{snapshot.timestamp.strftime('%H:%M:%S')}] 스냅샷 #{self.snapshot_count}")
        print(f"스레드 수: {snapshot.thread_count}")
        print(f"{'=' * 60}")

        blocked = snapshot.get_blocked_threads()
        if blocked:
            print(f"\n[블로킹된 스레드: {len(blocked)}개]")
            for thread in blocked:
                print(f"\n  {thread.thread_name} ({thread.thread_id})")
                print(f"  해시: {thread.stack_hash}")
                for i, frame in enumerate(thread.stack_frames[:5]):
                    prefix = "  → " if i == 0 else "    "
                    print(f"{prefix}{frame}")

        if self.verbose:
            print(f"\n[전체 스레드]")
            for thread in snapshot.threads:
                status = "[BLOCKED]" if thread.is_blocked() else ""
                print(f"  {thread.thread_name}: {thread.top_frame} {status}")

    def print_deadlock_alert(self, detection_result: dict) -> None:
        """데드락 알림 출력"""
        print(f"\n{'!' * 60}")
        print(f"{'!' * 20} 데드락 감지! {'!' * 20}")
        print(f"{'!' * 60}")
        print(f"신뢰도: {detection_result['confidence'] * 100:.0f}%")
        print(f"상세: {', '.join(detection_result['details'])}")

        print(f"\n[의심 스레드]")
        for thread_info in detection_result["suspected_threads"]:
            print(f"\n  스레드: {thread_info['thread_name']} ({thread_info['thread_id']})")
            print(f"  위치: {thread_info['top_frame']}")
            print(f"  블로킹 횟수: {thread_info['blocked_count']}회 연속")

        print(f"\n{'!' * 60}")

    def take_snapshot(self) -> Optional[ProcessSnapshot]:
        """스냅샷 촬영"""
        raw_output = self.run_py_spy_dump()
        if not raw_output:
            return None

        snapshot = self.parse_dump(raw_output)
        self.snapshot_count += 1

        return snapshot

    def run_once(self) -> dict:
        """단일 실행 (현재 상태만 확인)"""
        print(f"[정보] PID {self.pid} 분석 중...")

        snapshot = self.take_snapshot()
        if not snapshot:
            return {"error": "스냅샷 실패"}

        self.print_snapshot(snapshot)

        return {
            "thread_count": snapshot.thread_count,
            "blocked_count": len(snapshot.get_blocked_threads()),
            "threads": [
                {
                    "name": t.thread_name,
                    "blocked": t.is_blocked(),
                    "top_frame": t.top_frame
                }
                for t in snapshot.threads
            ]
        }

    def run_detection(self) -> dict:
        """데드락 감지 실행 (threshold 횟수만큼 샘플링)"""
        print(f"[정보] PID {self.pid} 데드락 감지 시작")
        print(f"[정보] 간격: {self.interval}초, 임계값: {self.threshold}회")
        print(f"[정보] 총 소요 시간: 약 {self.interval * self.threshold:.0f}초")

        last_snapshot: Optional[ProcessSnapshot] = None

        for i in range(self.threshold):
            print(f"\n[{i + 1}/{self.threshold}] 샘플링...")

            last_snapshot = self.take_snapshot()
            if not last_snapshot:
                continue

            self.print_snapshot(last_snapshot)

            # 마지막이 아니면 대기
            if i < self.threshold - 1:
                time.sleep(self.interval)

        # 최종 분석
        if self.snapshot_count > 0 and last_snapshot:
            result = self.detect_deadlock(last_snapshot)

            if result["is_deadlock"]:
                self.print_deadlock_alert(result)
            else:
                print(f"\n[결과] 데드락이 감지되지 않았습니다.")

            return result

        return {"error": "스냅샷 없음"}

    def run_watch(self) -> None:
        """연속 모니터링 모드"""
        print(f"[정보] PID {self.pid} 연속 모니터링 시작")
        print(f"[정보] 간격: {self.interval}초, 임계값: {self.threshold}회")
        print(f"[정보] 중지: Ctrl+C")

        try:
            while True:
                snapshot = self.take_snapshot()
                if not snapshot:
                    time.sleep(self.interval)
                    continue

                self.print_snapshot(snapshot)

                # 충분한 히스토리가 쌓이면 데드락 감지
                if self.snapshot_count >= self.threshold:
                    result = self.detect_deadlock(snapshot)

                    if result["is_deadlock"]:
                        self.print_deadlock_alert(result)

                        # 알림 후에도 계속 모니터링
                        print("\n[정보] 모니터링 계속 중...")

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print(f"\n\n[정보] 모니터링 종료")
            print(f"[정보] 총 {self.snapshot_count}개 스냅샷 수집")


def main():
    parser = argparse.ArgumentParser(
        description="py-spy를 활용한 데드락 감지 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 단일 스냅샷 (현재 상태 확인)
  python deadlock_detector.py 12345 --once

  # 데드락 감지 (기본: 5초 간격, 3회 샘플링)
  python deadlock_detector.py 12345

  # 커스텀 설정으로 데드락 감지
  python deadlock_detector.py 12345 --interval 3 --threshold 5

  # 연속 모니터링 모드
  python deadlock_detector.py 12345 --watch

  # 상세 출력
  python deadlock_detector.py 12345 --watch --verbose
        """
    )

    parser.add_argument(
        "pid",
        type=int,
        help="모니터링할 프로세스 ID"
    )

    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=5.0,
        help="샘플링 간격 (초, 기본값: 5.0)"
    )

    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=3,
        help="데드락 판단 임계값 (연속 동일 스택 횟수, 기본값: 3)"
    )

    parser.add_argument(
        "--once", "-1",
        action="store_true",
        help="단일 스냅샷만 수집 (데드락 감지 없이 현재 상태만 출력)"
    )

    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="연속 모니터링 모드 (Ctrl+C로 종료)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 출력"
    )

    args = parser.parse_args()

    # 프로세스 존재 확인
    try:
        import os
        os.kill(args.pid, 0)
    except ProcessLookupError:
        print(f"[오류] PID {args.pid} 프로세스가 존재하지 않습니다.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        # 프로세스는 존재하지만 권한 없음 (정상)
        pass

    detector = DeadlockDetector(
        pid=args.pid,
        interval=args.interval,
        threshold=args.threshold,
        verbose=args.verbose
    )

    if args.once:
        detector.run_once()
    elif args.watch:
        detector.run_watch()
    else:
        detector.run_detection()


if __name__ == "__main__":
    main()
