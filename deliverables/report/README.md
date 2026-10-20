# CBP 아이디어 상세보고서

**27쪽 PDF**로 문제 정의, 원안 계승·수정, 전체 운영 절차, 기호·단위, 예산 회계, 후보 제약, 모드, 수식, 모든 가상 계산, 예외, 경제적 해석, 민감도, 구현, 검증, 데이터, 실증, 지표, 한계, 질의응답과 자료 근거를 정리했습니다.

- [PDF 다운로드](https://github.com/shshwk33-stack/UNIT/raw/refs/heads/cbp-final-review-20261019/deliverables/report/cbp-idea-report.pdf)
- [PDF 보기](cbp-idea-report.pdf)
- [검수 기록](verification.json)

기준은 CBP V4입니다. `basis/`에 같은 버전의 모형·입력·데모를 보존했습니다. 수치는 설명용 가정이며 현장 성과로 해석하지 않습니다. 외부 선행 연구·수상작 원문 비교는 접근 제한으로 완료하지 못했음을 보고서에 명시했습니다.

수식 12개 결과를 독립 분수 연산으로 대조하고, 예산 갱신·단위 환산을 확인했습니다. PDF 27쪽의 제목·글자 범위·25개 목차 링크·글꼴 포함·레이아웃을 점검했고, 모든 페이지를 렌더링해 검토했습니다. 보고서 검수는 현장 유효성이나 신규성 입증과 구분됩니다.

원본 HTML과 생성 스크립트도 함께 보관합니다. PDF는 단독으로 읽을 수 있습니다.

## 재생성

Python 3, numpy, matplotlib, PyMuPDF, Node.js, Playwright, Chromium, Noto Sans CJK 글꼴, pdffonts가 필요합니다.

```bash
MPLCONFIGDIR=/tmp/cbp-report-mpl python make_figure.py
python build_report.py
node render_report.cjs
python verify_report.py
```

다른 환경에서는 글꼴·Chromium 경로를 조정할 수 있습니다. 생성 과정의 로컬 서버는 PDF 출력 후 종료합니다.
