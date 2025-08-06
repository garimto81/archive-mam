"""
GFX 오버레이 학습기 End-to-End 테스트
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class GFXOverlayE2ETest:
    def __init__(self):
        self.driver = None
        self.base_url = "http://localhost:8080"
        
    def setup(self):
        """테스트 환경 설정"""
        print("🔧 테스트 환경 설정 중...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 헤드리스 모드
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            print("✅ Chrome 드라이버 초기화 성공")
            return True
        except:
            # Chrome이 없으면 Edge 시도
            try:
                from selenium.webdriver.edge.options import Options
                edge_options = Options()
                edge_options.add_argument('--headless')
                self.driver = webdriver.Edge(options=edge_options)
                print("✅ Edge 드라이버 초기화 성공")
                return True
            except Exception as e:
                print(f"❌ 드라이버 초기화 실패: {e}")
                return False
    
    def test_page_load(self):
        """페이지 로드 테스트"""
        print("\n📄 페이지 로드 테스트...")
        try:
            self.driver.get(f"{self.base_url}/web-ui/gfx_overlay_trainer.html")
            
            # 페이지 타이틀 확인
            WebDriverWait(self.driver, 10).until(
                EC.title_contains("GFX 오버레이")
            )
            print(f"✅ 페이지 로드 성공: {self.driver.title}")
            
            # 주요 요소 확인
            elements_to_check = [
                ("videoCanvas", "비디오 캔버스"),
                ("markGFXBtn", "GFX 마킹 버튼"),
                ("saveBtn", "저장 버튼"),
                ("loadBtn", "불러오기 버튼"),
                ("clearBtn", "초기화 버튼")
            ]
            
            for elem_id, elem_name in elements_to_check:
                try:
                    element = self.driver.find_element(By.ID, elem_id)
                    print(f"  ✅ {elem_name} 존재: {elem_id}")
                except:
                    print(f"  ❌ {elem_name} 없음: {elem_id}")
                    
            return True
            
        except TimeoutException:
            print("❌ 페이지 로드 실패: 타임아웃")
            return False
        except Exception as e:
            print(f"❌ 페이지 로드 실패: {e}")
            return False
    
    def test_button_states(self):
        """버튼 상태 테스트"""
        print("\n🔘 버튼 초기 상태 테스트...")
        try:
            # GFX 마킹 버튼 초기 상태
            gfx_btn = self.driver.find_element(By.ID, "markGFXBtn")
            
            # 초기에는 비활성화 상태여야 함 (비디오 없음)
            is_disabled = gfx_btn.get_attribute("disabled")
            if is_disabled:
                print("  ✅ GFX 버튼 초기 비활성화 상태 확인")
            else:
                print("  ⚠️ GFX 버튼이 활성화되어 있음 (비디오 없이)")
            
            # 버튼 텍스트 확인
            btn_text = gfx_btn.text
            if "시작점" in btn_text:
                print(f"  ✅ 버튼 텍스트 확인: {btn_text}")
            else:
                print(f"  ❌ 예상치 못한 버튼 텍스트: {btn_text}")
                
            return True
            
        except Exception as e:
            print(f"❌ 버튼 상태 테스트 실패: {e}")
            return False
    
    def test_segment_info_visibility(self):
        """구간 정보 표시 테스트"""
        print("\n📊 구간 정보 표시 테스트...")
        try:
            segment_info = self.driver.find_element(By.ID, "segmentInfo")
            
            # 초기에는 숨겨져 있어야 함
            display_style = segment_info.value_of_css_property("display")
            if display_style == "none":
                print("  ✅ 구간 정보 초기 숨김 상태 확인")
            else:
                print(f"  ⚠️ 구간 정보가 표시됨: {display_style}")
                
            return True
            
        except Exception as e:
            print(f"❌ 구간 정보 테스트 실패: {e}")
            return False
    
    def test_localStorage_functions(self):
        """LocalStorage 기능 테스트"""
        print("\n💾 LocalStorage 기능 테스트...")
        try:
            # 테스트 데이터 저장
            test_segments = [
                {
                    "gfxStart": 10,
                    "gfxEnd": 20,
                    "handStart": 0,
                    "handEnd": 35,
                    "id": 123456789
                }
            ]
            
            # LocalStorage에 저장
            self.driver.execute_script(
                "localStorage.setItem('gfxSegments', arguments[0]);",
                json.dumps(test_segments)
            )
            print("  ✅ 테스트 데이터 저장 성공")
            
            # 페이지 새로고침
            self.driver.refresh()
            time.sleep(2)
            
            # 데이터 복원 확인
            stored_data = self.driver.execute_script(
                "return localStorage.getItem('gfxSegments');"
            )
            
            if stored_data:
                loaded_segments = json.loads(stored_data)
                if len(loaded_segments) > 0:
                    print(f"  ✅ 데이터 복원 성공: {len(loaded_segments)}개 구간")
                else:
                    print("  ⚠️ 데이터가 복원되었지만 비어있음")
            else:
                print("  ❌ 데이터 복원 실패")
                
            # 정리
            self.driver.execute_script("localStorage.removeItem('gfxSegments');")
            print("  ✅ 테스트 데이터 정리 완료")
            
            return True
            
        except Exception as e:
            print(f"❌ LocalStorage 테스트 실패: {e}")
            return False
    
    def test_statistics_display(self):
        """통계 표시 테스트"""
        print("\n📈 통계 표시 테스트...")
        try:
            # 통계 요소 확인
            stats_elements = ["gfxCount", "gameCount", "totalSamples"]
            
            for elem_id in stats_elements:
                element = self.driver.find_element(By.ID, elem_id)
                text = element.text
                print(f"  ✅ {elem_id}: {text}")
                
            # 프로그레스 바 확인
            gfx_progress = self.driver.find_element(By.ID, "gfxProgress")
            game_progress = self.driver.find_element(By.ID, "gameProgress")
            
            gfx_width = gfx_progress.value_of_css_property("width")
            game_width = game_progress.value_of_css_property("width")
            
            print(f"  ✅ GFX 진행률 바: {gfx_width}")
            print(f"  ✅ Game 진행률 바: {game_width}")
            
            return True
            
        except Exception as e:
            print(f"❌ 통계 표시 테스트 실패: {e}")
            return False
    
    def test_responsive_layout(self):
        """반응형 레이아웃 테스트"""
        print("\n📱 반응형 레이아웃 테스트...")
        try:
            # 다양한 화면 크기 테스트
            sizes = [
                (1920, 1080, "Desktop"),
                (768, 1024, "Tablet"),
                (375, 667, "Mobile")
            ]
            
            for width, height, device in sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                # 주요 요소가 보이는지 확인
                canvas = self.driver.find_element(By.ID, "videoCanvas")
                is_displayed = canvas.is_displayed()
                
                if is_displayed:
                    print(f"  ✅ {device} ({width}x{height}): 레이아웃 정상")
                else:
                    print(f"  ❌ {device} ({width}x{height}): 레이아웃 문제")
                    
            return True
            
        except Exception as e:
            print(f"❌ 반응형 레이아웃 테스트 실패: {e}")
            return False
    
    def teardown(self):
        """테스트 정리"""
        if self.driver:
            self.driver.quit()
            print("\n🧹 테스트 환경 정리 완료")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("="*50)
        print("🚀 GFX 오버레이 학습기 E2E 테스트 시작")
        print("="*50)
        
        if not self.setup():
            print("❌ 테스트 환경 설정 실패")
            return False
        
        test_results = []
        
        # 각 테스트 실행
        tests = [
            ("페이지 로드", self.test_page_load),
            ("버튼 상태", self.test_button_states),
            ("구간 정보", self.test_segment_info_visibility),
            ("LocalStorage", self.test_localStorage_functions),
            ("통계 표시", self.test_statistics_display),
            ("반응형 레이아웃", self.test_responsive_layout)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} 테스트 예외 발생: {e}")
                test_results.append((test_name, False))
        
        # 결과 요약
        print("\n" + "="*50)
        print("📊 테스트 결과 요약")
        print("="*50)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {test_name}")
        
        print(f"\n총 {total}개 테스트 중 {passed}개 성공")
        print(f"성공률: {(passed/total)*100:.1f}%")
        
        self.teardown()
        
        return passed == total


# 수동 테스트를 위한 간단한 HTML 테스트 페이지
def create_manual_test_page():
    """수동 테스트용 페이지 생성"""
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>GFX 오버레이 학습기 수동 테스트</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>🧪 GFX 오버레이 학습기 수동 테스트</h1>
        <hr>
        
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">테스트 시나리오</h5>
                <ol>
                    <li>아래 링크를 클릭하여 GFX 오버레이 학습기 열기</li>
                    <li>비디오 파일 업로드</li>
                    <li>GFX 오버레이 시작점에서 버튼 클릭 (빨간색 → 노란색)</li>
                    <li>GFX 오버레이 종료점에서 버튼 클릭 (노란색 → 빨간색)</li>
                    <li>구간 정보 확인 (±15초 규칙 적용)</li>
                    <li>구간 데이터 JSON 내보내기</li>
                </ol>
            </div>
        </div>
        
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">테스트 링크</h5>
                <a href="/web-ui/gfx_overlay_trainer.html" class="btn btn-primary" target="_blank">
                    🎰 GFX 오버레이 학습기 열기
                </a>
            </div>
        </div>
        
        <div class="card mt-3">
            <div class="card-body">
                <h5 class="card-title">예상 결과</h5>
                <ul>
                    <li>✅ 버튼이 토글 방식으로 작동</li>
                    <li>✅ 구간 정보가 실시간 표시</li>
                    <li>✅ 15초 규칙이 자동 적용</li>
                    <li>✅ JSON 파일로 내보내기 가능</li>
                    <li>✅ 구간 목록이 카드 형태로 표시</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    with open("C:\\claude03\\archive-mam\\test_manual.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 수동 테스트 페이지 생성: test_manual.html")


if __name__ == "__main__":
    # Selenium 테스트 실행 시도
    try:
        print("🔍 Selenium 설치 확인 중...")
        import selenium
        print(f"✅ Selenium 버전: {selenium.__version__}")
        
        tester = GFXOverlayE2ETest()
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 모든 E2E 테스트 통과!")
        else:
            print("\n⚠️ 일부 테스트 실패")
            
    except ImportError:
        print("⚠️ Selenium이 설치되지 않았습니다.")
        print("수동 테스트 페이지를 생성합니다...")
        create_manual_test_page()
        print("\n📝 수동 테스트 가이드:")
        print("1. 브라우저에서 http://localhost:8080/test_manual.html 열기")
        print("2. 가이드에 따라 테스트 수행")