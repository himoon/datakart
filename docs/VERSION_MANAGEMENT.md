# 버전 관리 가이드

`datakart` 패키지의 버전은 Git 태그를 기반으로 자동으로 관리됩니다.
**버전 형식: X.Y** (예: 1.0, 1.1, 2.0)

## 🚀 빠른 시작

### 1단계: 버전 릴리스 실행
```bash
./scripts/release.sh
```

이 스크립트는 다음을 수행합니다:
- **현재 버전 확인**: 가장 최근의 Git 태그를 기반으로 현재 버전을 파악합니다.
- **릴리스 유형 선택**:
    - **Minor** (X.Y+1): 새 기능 추가 또는 버그 수정 (두 번째 숫자 증가)
    - **Major** (X+1.0): 주요 변경 또는 호환성이 깨지는 변경 (첫 번째 숫자 증가)
- **태그 생성**: 로컬 Git 저장소에 새 버전 태그(예: `v1.2`)를 생성합니다.
- **자동 푸시**: 스크립트 마지막에 원격(`origin`)으로 즉시 푸시할지 선택할 수 있습니다.

### 2단계: 자동화 (GitHub Actions)
원격으로 푸시된 태그를 감지하여 GitHub Actions가 자동으로 다음을 수행합니다:
- ✅ **테스트 실행**: Python 3.12 ~ 3.14 환경에서 모든 테스트 검증
- 📦 **PyPI 배포**: OIDC(Trusted Publishing)를 통해 안전하게 배포
- 📝 **GitHub Release 생성**: 빌드된 배포 파일(`.whl`, `.tar.gz`)을 포함한 릴리스 페이지 생성

---

## 🌟 최초 릴리스 가이드 (처음 시작할 때)

Git 태그를 한 번도 사용하지 않았더라도 걱정하지 마세요. 스크립트가 알아서 처리해 드립니다.

1.  **코드 정리**: 모든 변경사항을 커밋하고 `main` 브랜치로 이동합니다.
    ```bash
    git add .
    git commit -m "feat: 초기 기능 완성"
    git checkout main
    ```
2.  **PyPI OIDC 설정**: 위의 **[🔐 PyPI 배포 설정 (OIDC)]** 섹션을 참고하여 PyPI 사이트에서 저장소를 등록합니다. (이 작업이 완료되어야 배포가 성공합니다.)
3.  **릴리스 스크립트 실행**:
    ```bash
    ./scripts/release.sh
    ```
    *   스크립트가 기존 태그를 찾지 못하면 자동으로 **현재 버전을 `0.1`로 간주**합니다.
    *   첫 정식 릴리스를 `1.0`으로 하고 싶다면 **2. Major**를 선택하세요.
    *   베타 버전처럼 시작하고 싶다면 **1. Minor (0.2)**를 선택하세요.
4.  **확인 및 푸시**: 스크립트 마지막 단계에서 `y`를 눌러 원격으로 푸시합니다.
5.  **결과 확인**: GitHub 저장소의 **Actions** 탭에서 배포 과정을 실시간으로 확인할 수 있습니다.

---

## 📋 동작 원리

### 버전 소스: Git 태그
```
Git Tag: v1.2
  ↓
pyproject.toml (hatch-vcs)에서 태그 정보를 읽음
  ↓
패키지 빌드 시 자동으로 버전 주입
```

### 코드에서 버전 확인
```python
import datakart
print(datakart.__version__)  # 예: "1.2"
```
*내부적으로 `importlib.metadata` 표준 라이브러리를 사용하여 설치된 패키지 정보를 읽어옵니다.*

---

## 🔧 설정 파일

| 파일 | 역할 |
|---|---|
| `.github/workflows/publish.yml` | CI/CD: 테스트 → 빌드 → PyPI 배포 (OIDC 기반) |
| `pyproject.toml` | `hatch-vcs` 및 최신 Python (>=3.12) 지원 설정 |
| `src/datakart/__init__.py` | `__version__` 동적 로드 (표준 라이브러리 사용) |
| `scripts/release.sh` | 로컬 버전 관리 및 릴리스 자동화 스크립트 |

---

## 🔐 PyPI 배포 설정 (OIDC)

이제 더 이상 위험한 API 토큰(`PYPI_API_TOKEN`)을 GitHub Secrets에 저장할 필요가 없습니다. **Trusted Publishing (OIDC)** 방식을 사용합니다.

### PyPI 웹사이트 설정 (최초 1회)
1. [PyPI Publishing](https://pypi.org/manage/account/publishing/) 페이지로 이동합니다.
2. **"Add a new publisher"**에서 **GitHub**를 선택합니다.
3. 다음 정보를 입력합니다:
   - **Owner**: `himoon` (사용자 아이디)
   - **Repository**: `datakart` (저장소 이름)
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

---

## 💡 예시

### 일반적인 기능 추가 (1.0 → 1.1)
```bash
./scripts/release.sh  # → 1. Minor 선택 → 푸시 동의(y)
```

### 대규모 업데이트 (1.1 → 2.0)
```bash
./scripts/release.sh  # → 2. Major 선택 → 푸시 동의(y)
```

---

## ❓ 문제 해결

### Q: "PackageNotFoundError" 에러가 나요
패키지가 `pip` 등으로 정식 설치되지 않은 개발 환경에서 `__version__`을 호출하면 발생할 수 있습니다. 이 경우 기본값인 `0.0.0.dev0`이 표시됩니다.

### Q: 특정 태그를 취소하고 싶어요
```bash
# 로컬 태그 삭제
git tag -d v1.2
# 원격 태그 삭제
git push origin --delete v1.2
```

### Q: 왜 세 자리가 아닌 두 자리(X.Y) 버전인가요?
단순함을 유지하기 위해 패치(Patch) 버전을 생략하고 Major.Minor 체계로 관리합니다. 버그 수정은 Minor 버전을 올려서 배포합니다.

---

## 참고자료
- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [Hatch VCS Documentation](https://hatch.pypa.io/en/latest/plugins/version-source/vcs/)
