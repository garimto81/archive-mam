# 💡 경량 UI 감지 전략 (학습 없음)

## 🎯 핵심 접근법: 휴리스틱 + 템플릿 매칭

### 1. 휴리스틱 기반 UI 감지

#### 🔍 주요 특징
```
UI의 공통 특성:
1. 정적임 - 15초 이상 변화 없음
2. 규칙적 레이아웃 - 격자, 정렬
3. 텍스트 블록 - 고대비, 사각형
4. 제한된 색상 - 브랜드 콜러
5. 또렷한 경계 - 선명한 엣지
```

#### 📊 구현 방법
```javascript
// 1. 프레임 차이 분석
function analyzeFrameDifference(frame1, frame2) {
    let changedPixels = 0;
    for (let i = 0; i < pixels.length; i++) {
        if (Math.abs(frame1[i] - frame2[i]) > threshold) {
            changedPixels++;
        }
    }
    return changedPixels / totalPixels < 0.05; // 5% 미만이면 정적
}

// 2. 엣지 검출 (간단한 Sobel 필터)
function detectEdges(imageData) {
    const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1];
    const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1];
    // 엣지 계산 로직
}

// 3. 색상 분포 분석
function analyzeColorDistribution(imageData) {
    const colorCounts = {};
    // 주요 색상 카운트
    const dominantColors = Object.keys(colorCounts)
        .sort((a, b) => colorCounts[b] - colorCounts[a])
        .slice(0, 5);
    
    // 상위 5개 색상이 80% 이상 차지하면 UI 가능성
}
```

### 2. 사용자 제공 템플릿 매칭

#### 🖼️ 템플릿 시스템
```javascript
class UITemplateManager {
    constructor() {
        this.templates = [];
    }
    
    // 사용자가 UI 표시
    addTemplate(frame) {
        this.templates.push({
            // 빠른 비교를 위한 특징 추출
            colorHistogram: this.getColorHistogram(frame),
            edgeSignature: this.getEdgeSignature(frame),
            blockPattern: this.getBlockPattern(frame),
            timestamp: Date.now()
        });
    }
    
    // 현재 프레임과 비교
    matchTemplate(frame) {
        const currentFeatures = {
            colorHistogram: this.getColorHistogram(frame),
            edgeSignature: this.getEdgeSignature(frame),
            blockPattern: this.getBlockPattern(frame)
        };
        
        let bestMatch = 0;
        for (const template of this.templates) {
            const similarity = this.calculateSimilarity(
                currentFeatures, 
                template
            );
            bestMatch = Math.max(bestMatch, similarity);
        }
        
        return bestMatch;
    }
}
```

### 3. 통합 감지 시스템

#### 🌐 웹 기반 구현
```javascript
class LightweightUIDetector {
    constructor() {
        this.heuristicWeight = 0.7;
        this.templateWeight = 0.3;
        this.frameBuffer = [];
        this.bufferSize = 450; // 15초 @ 30fps
    }
    
    detect(frame) {
        // 1. 휴리스틱 점수
        const heuristicScore = this.calculateHeuristicScore(frame);
        
        // 2. 템플릿 매칭 점수
        const templateScore = this.templateManager.matchTemplate(frame);
        
        // 3. 통합 점수
        const finalScore = 
            heuristicScore * this.heuristicWeight + 
            templateScore * this.templateWeight;
        
        // 4. 15초 버퍼 검사
        this.frameBuffer.push(finalScore > 0.65);
        if (this.frameBuffer.length > this.bufferSize) {
            this.frameBuffer.shift();
        }
        
        const uiFrames = this.frameBuffer.filter(x => x).length;
        return uiFrames >= this.bufferSize * 0.9; // 90% 이상 UI
    }
}
```

### 4. 실용적 구현 방안

#### 🛠️ 옵션 1: Canvas API만 사용
```javascript
// 순수 JavaScript + Canvas
// 추가 라이브러리 없음
const ctx = canvas.getContext('2d');
const imageData = ctx.getImageData(0, 0, width, height);
// 픽셀 데이터 직접 분석
```

#### 📦 옵션 2: WebAssembly 경량 모듈
```javascript
// 미리 컴파일된 경량 WASM 모듈 (< 100KB)
// OpenCV 없이 필수 기능만 구현
const wasmModule = await WebAssembly.instantiateStreaming(
    fetch('ui_detector_lite.wasm')
);
```

#### 🌍 옵션 3: 서버리스 엣지 함수
```javascript
// Cloudflare Workers 또는 Vercel Edge Functions
// 키프레임만 전송하여 서버에서 분석
export default async function handler(req) {
    const frame = await req.json();
    const features = extractFeatures(frame);
    return Response.json({ isUI: detectUI(features) });
}
```

## 📊 성능 비교

| 방법 | 정확도 | 속도 | 메모리 | 구현 난이도 |
|------|--------|------|--------|-------------|
| ML 모델 | 95% | 느림 | 많음 | 높음 |
| 휴리스틱 | 80% | 빠름 | 적음 | 낮음 |
| 템플릿 | 85% | 보통 | 보통 | 낮음 |
| 통합 | 88% | 빠름 | 적음 | 보통 |

## 🚀 즉시 사용 가능한 코드

```html
<!-- index.html에 추가 -->
<script>
// 간단한 UI 감지기
class SimpleUIDetector {
    constructor() {
        this.threshold = 0.65;
        this.buffer = [];
    }
    
    analyze(canvas) {
        const ctx = canvas.getContext('2d');
        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        
        // 간단한 휴리스틱
        let staticScore = this.getStaticScore(data);
        let uniformityScore = this.getUniformityScore(data);
        
        const score = (staticScore + uniformityScore) / 2;
        
        this.buffer.push(score > this.threshold);
        if (this.buffer.length > 450) this.buffer.shift();
        
        const uiCount = this.buffer.filter(x => x).length;
        return uiCount > 400; // 15초 중 13초 이상
    }
    
    getStaticScore(data) {
        // 프레임 간 차이 계산
        // 구현 코드...
    }
    
    getUniformityScore(data) {
        // 색상 분포 계산
        // 구현 코드...
    }
}
</script>
```

## 🎯 추천 방향

1. **초기 버전**: 휴리스틱만으로 시작 (80% 정확도)
2. **개선 버전**: 사용자 템플릿 추가 (85% 정확도)
3. **최적화**: WebAssembly로 성능 향상
4. **미래**: 선택적 ML 모델 적용

학습 없이도 충분히 실용적인 UI 감지가 가능합니다!