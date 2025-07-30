#!/usr/bin/env python
"""
프론트엔드 자동화 테스트
Selenium을 사용한 E2E 테스트
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FrontendTester:
    """프론트엔드 자동화 테스트"""
    
    def __init__(self, headless=False):
        """Chrome 드라이버 초기화"""
        self.driver = None
        self.base_url = "http://localhost:3000"
        self.headless = headless
        self.test_results = []
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            print(f"❌ Chrome 드라이버 초기화 실패: {e}")
            print("Chrome과 ChromeDriver가 설치되어 있는지 확인하세요.")
            return False
    
    def teardown_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
    
    def log_test(self, test_name, success, message=""):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_page_load(self, path="/", expected_title_contains="Poker"):
        """페이지 로딩 테스트"""
        try:
            self.driver.get(f"{self.base_url}{path}")
            
            # 페이지 제목 확인
            WebDriverWait(self.driver, 10).until(
                lambda driver: expected_title_contains.lower() in driver.title.lower()
            )
            
            self.log_test(f"페이지 로딩 ({path})", True, f"제목: {self.driver.title}")
            return True
        except TimeoutException:
            self.log_test(f"페이지 로딩 ({path})", False, f"제목 확인 실패: {self.driver.title}")
            return False
        except Exception as e:
            self.log_test(f"페이지 로딩 ({path})", False, str(e))
            return False
    
    def test_navigation(self):
        """네비게이션 메뉴 테스트"""
        try:
            self.driver.get(self.base_url)
            
            # 메뉴 항목들 확인
            menu_items = [
                ("대시보드", "/dashboard"),
                ("영상 관리", "/videos"),
                ("영상 업로드", "/videos/upload"),
                ("핸드 라이브러리", "/hands")
            ]
            
            for menu_text, expected_path in menu_items:
                try:
                    # 메뉴 클릭
                    menu_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, menu_text))
                    )
                    menu_link.click()
                    
                    # URL 변경 확인
                    time.sleep(1)
                    current_url = self.driver.current_url
                    
                    if expected_path in current_url:
                        self.log_test(f"네비게이션 - {menu_text}", True, f"URL: {current_url}")
                    else:
                        self.log_test(f"네비게이션 - {menu_text}", False, f"예상 경로 {expected_path}와 다름: {current_url}")
                
                except TimeoutException:
                    self.log_test(f"네비게이션 - {menu_text}", False, "메뉴 요소를 찾을 수 없음")
                
                except Exception as e:
                    self.log_test(f"네비게이션 - {menu_text}", False, str(e))
        
        except Exception as e:
            self.log_test("네비게이션 전체", False, str(e))
    
    def test_dashboard_content(self):
        """대시보드 콘텐츠 테스트"""
        try:
            self.driver.get(f"{self.base_url}/dashboard")
            
            # 통계 카드들 확인
            stats_elements = [
                "전체 영상",
                "전체 핸드",
                "평균 핸드/영상",
                "처리 중"
            ]
            
            for stat_text in stats_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{stat_text}')]"))
                    )
                    self.log_test(f"대시보드 - {stat_text}", True, "요소 발견")
                except TimeoutException:
                    self.log_test(f"대시보드 - {stat_text}", False, "요소를 찾을 수 없음")
        
        except Exception as e:
            self.log_test("대시보드 콘텐츠", False, str(e))
    
    def test_responsive_design(self):
        """반응형 디자인 테스트"""
        viewport_sizes = [
            (1920, 1080, "Desktop"),
            (768, 1024, "Tablet"),
            (375, 667, "Mobile")
        ]
        
        for width, height, device in viewport_sizes:
            try:
                self.driver.set_window_size(width, height)
                self.driver.get(f"{self.base_url}/dashboard")
                time.sleep(2)
                
                # 기본 요소가 보이는지 확인
                try:
                    header = self.driver.find_element(By.TAG_NAME, "h1")
                    if header.is_displayed():
                        self.log_test(f"반응형 - {device} ({width}x{height})", True, "헤더 요소 표시됨")
                    else:
                        self.log_test(f"반응형 - {device} ({width}x{height})", False, "헤더 요소가 숨겨져 있음")
                except NoSuchElementException:
                    self.log_test(f"반응형 - {device} ({width}x{height})", False, "헤더 요소를 찾을 수 없음")
            
            except Exception as e:
                self.log_test(f"반응형 - {device}", False, str(e))
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        if not self.setup_driver():
            return False
        
        print("프론트엔드 자동화 테스트 시작...")
        print("=" * 50)
        
        try:
            # 기본 페이지 로딩 테스트
            self.test_page_load("/", "Poker")
            
            # 네비게이션 테스트
            self.test_navigation()
            
            # 대시보드 콘텐츠 테스트
            self.test_dashboard_content()
            
            # 반응형 디자인 테스트
            self.test_responsive_design()
            
        finally:
            self.teardown_driver()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("테스트 결과 요약:")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}개")
        print(f"성공: {passed_tests}개")
        print(f"실패: {failed_tests}개")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        return failed_tests == 0


def check_prerequisites():
    """테스트 실행 전 필수 조건 확인"""
    print("필수 조건 확인 중...")
    
    # 백엔드 서버 확인
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:8000/")
            if response.status_code == 200:
                print("✅ 백엔드 서버 실행 중")
            else:
                print("❌ 백엔드 서버 응답 오류")
                return False
    except Exception:
        print("❌ 백엔드 서버에 연결할 수 없습니다")
        print("   run_test_server.bat를 실행해주세요")
        return False
    
    # 프론트엔드 서버 확인
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:3000/")
            if response.status_code == 200:
                print("✅ 프론트엔드 서버 실행 중")
            else:
                print("❌ 프론트엔드 서버 응답 오류")
                return False
    except Exception:
        print("❌ 프론트엔드 서버에 연결할 수 없습니다")
        print("   cd frontend && npm start를 실행해주세요")
        return False
    
    return True


if __name__ == "__main__":
    if not check_prerequisites():
        print("\n필수 조건이 충족되지 않았습니다.")
        exit(1)
    
    # 헤드리스 모드 옵션
    import sys
    headless = "--headless" in sys.argv
    
    tester = FrontendTester(headless=headless)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)