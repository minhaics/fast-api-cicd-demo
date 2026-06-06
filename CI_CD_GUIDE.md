# CI/CD Demo Thực Tế Với GitHub Actions Và MacBook Local

Mục tiêu: làm thử một luồng CI/CD miễn phí, gần giống thực tế, nhưng không cần VPS.

Trong demo này:

```text
GitHub repo                 giữ source code
GitHub Actions              chạy pipeline
GitHub Container Registry   giữ Docker image
MacBook local               làm server deploy bằng self-hosted runner
```

Flow cuối cùng:

```text
Bạn sửa code
  -> git push main
  -> GitHub Actions chạy test
  -> GitHub Actions build Docker image
  -> GitHub Actions push image lên GHCR
  -> GitHub gửi deploy job về MacBook
  -> MacBook pull image mới
  -> MacBook stop container cũ
  -> MacBook run container mới
  -> app chạy ở http://localhost:8000
```

Điểm quan trọng:

```text
Không cần VPS.
Không cần tunnel.
Không cần mở port router.
MacBook chủ động kết nối ra GitHub để nhận job.
```

## 1. Luồng CI/CD Này Có Những Phần Nào?

### CI

CI kiểm tra code:

```text
checkout source code
setup Python
install dependencies
pytest -q
```

Nếu test fail, pipeline dừng.

### Build/Release

Nếu test pass:

```text
build Docker image
push image lên ghcr.io
```

Image sẽ nằm ở:

```text
ghcr.io/<github-owner>/notes-cicd-demo:latest
```

### CD

Deploy job chạy trên MacBook self-hosted runner:

```text
docker pull image mới
docker stop container cũ
docker rm container cũ
docker run container mới
```

App chạy ở:

```text
http://localhost:8000
```

## 2. Chuẩn Bị Trên MacBook

Cần có:

```text
Docker Desktop
Git
Python 3
GitHub account
Repo GitHub chứa project này
```

Kiểm tra Docker:

```bash
docker ps
```

Nếu lỗi, mở Docker Desktop trước.

Kiểm tra app local:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Nếu `pytest -q` fail thì sửa trước khi làm CI/CD.

## 3. Push Project Lên GitHub

Nếu project chưa phải git repo:

```bash
git init
git branch -M main
git add .
git commit -m "Add FastAPI CI/CD demo"
```

Tạo repo trên GitHub, rồi chạy:

```bash
git remote add origin git@github.com:<username>/<repo>.git
git push -u origin main
```

Sau khi push, mở:

```text
GitHub repo -> Actions
```

Bạn sẽ thấy workflow `CI/CD`.

## 4. Tạo Self-hosted Runner Trên MacBook

Vào GitHub repo:

```text
Settings -> Actions -> Runners -> New self-hosted runner
```

Chọn:

```text
macOS
```

GitHub sẽ hiện một nhóm lệnh cài runner. Copy đúng lệnh GitHub đưa cho bạn.

Ví dụ dạng lệnh sẽ giống:

```bash
mkdir actions-runner
cd actions-runner
curl -o actions-runner-osx-arm64.tar.gz -L <github-runner-download-url>
tar xzf ./actions-runner-osx-arm64.tar.gz
./config.sh --url https://github.com/<username>/<repo> --token <token>
```

Sau khi config xong, chạy runner:

```bash
./run.sh
```

Khi terminal hiện:

```text
Listening for Jobs
```

nghĩa là MacBook đã sẵn sàng nhận job từ GitHub Actions.

Lưu ý:

```text
Terminal chạy ./run.sh phải đang mở.
Docker Desktop phải đang chạy.
MacBook phải có internet.
```

## 5. Cập Nhật Workflow Để Deploy Trên MacBook

File cần sửa:

```text
.github/workflows/ci-cd.yml
```

Workflow nên có 3 job:

```text
test
build-and-push
deploy-local
```

Job `test` và `build-and-push` chạy trên GitHub runner.

Job `deploy-local` chạy trên MacBook:

```yaml
runs-on: self-hosted
```

Ví dụ workflow đầy đủ:

```yaml
name: CI/CD

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  test:
    name: Test FastAPI app
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -q

  build-and-push:
    name: Build and push Docker image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Checkout source
        uses: actions/checkout@v4

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository_owner }}/notes-cicd-demo:latest

  deploy-local:
    name: Deploy on local MacBook
    runs-on: self-hosted
    needs: build-and-push
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Login to GitHub Container Registry
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin

      - name: Pull latest image
        run: docker pull ghcr.io/${{ github.repository_owner }}/notes-cicd-demo:latest

      - name: Replace running container
        run: |
          docker stop notes-cicd-demo || true
          docker rm notes-cicd-demo || true
          docker run -d \
            --name notes-cicd-demo \
            --restart unless-stopped \
            -p 8000:8000 \
            -v notes-cicd-data:/app/data \
            ghcr.io/${{ github.repository_owner }}/notes-cicd-demo:latest
```

Điểm cần hiểu:

```text
runs-on: ubuntu-latest   job chạy trên máy GitHub
runs-on: self-hosted     job chạy trên MacBook của bạn
```

## 6. Chạy Demo End-to-End

Đảm bảo runner đang chạy:

```bash
cd actions-runner
./run.sh
```

Ở terminal khác, trong project:

```bash
pytest -q
git add .
git commit -m "Configure local self-hosted deploy"
git push
```

Mở GitHub:

```text
Repo -> Actions -> CI/CD -> run mới nhất
```

Bạn sẽ thấy:

```text
test             chạy trên ubuntu-latest
build-and-push   chạy trên ubuntu-latest
deploy-local     chạy trên self-hosted
```

Khi `deploy-local` chạy, terminal runner trên MacBook cũng sẽ hiện log nhận job.

Sau khi pipeline pass, kiểm tra app:

```bash
curl http://localhost:8000/health
```

Mở browser:

```text
http://localhost:8000
```

Nếu thấy app chạy, nghĩa là CI/CD demo thành công.

## 7. Demo Một Thay Đổi Code

Sửa version trong `app/main.py`:

```python
app = FastAPI(title="Notes CI/CD Demo", version="1.0.1", lifespan=lifespan)
```

Chạy test local:

```bash
pytest -q
```

Commit và push:

```bash
git add app/main.py
git commit -m "Update app version"
git push
```

Quan sát flow:

```text
GitHub Actions test pass
GitHub Actions build image mới
GHCR nhận image latest mới
MacBook self-hosted runner deploy image mới
container notes-cicd-demo được thay thế
```

Kiểm tra container:

```bash
docker ps
```

Kiểm tra API:

```bash
curl http://localhost:8000/health
```

## 8. Nếu Pipeline Fail Thì Xem Ở Đâu?

Vào:

```text
GitHub repo -> Actions -> CI/CD -> job bị fail
```

Nếu fail ở `test`:

```text
code lỗi
test lỗi
dependency thiếu
```

Nếu fail ở `build-and-push`:

```text
Dockerfile lỗi
pip install lỗi
không push được GHCR
```

Nếu fail ở `deploy-local`:

```text
runner chưa chạy
Docker Desktop chưa chạy
docker login ghcr.io lỗi
port 8000 đang bị chiếm
container cũ lỗi
```

Kiểm tra runner:

```text
GitHub repo -> Settings -> Actions -> Runners
```

Runner phải có trạng thái:

```text
Idle
```

hoặc đang nhận job.

## 9. Lưu Ý Bảo Mật

Chỉ dùng self-hosted runner cho repo bạn tin tưởng.

Lý do:

```text
Workflow có thể chạy command trên MacBook của bạn.
```

Không nên dùng self-hosted runner cho repo public có người lạ tạo pull request.

Khi học cá nhân, nên dùng:

```text
repo private
hoặc repo public nhưng không chạy self-hosted runner cho pull_request
```

Trong workflow phía trên, `deploy-local` chỉ chạy khi push vào `main`:

```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

## 10. Tóm Tắt

Bạn đang mô phỏng một hệ thống thật:

```text
Developer push code
CI test code
Build Docker image
Push image vào registry
Server pull image
Server restart container
```

Trong demo này:

```text
Developer = bạn
CI server = GitHub-hosted runner
Registry = GitHub Container Registry
Server = MacBook local
Deploy runner = GitHub Actions self-hosted runner trên MacBook
```

Đây là flow cần nhớ:

```text
git push main
  -> test
  -> build image
  -> push image
  -> deploy-local trên MacBook
  -> app chạy ở localhost:8000
```
