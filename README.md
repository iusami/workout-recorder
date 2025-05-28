# Docker Compose を使って全サービスをビルドして起動

docker compose up --build -d

# Nxコマンドでフロントエンドをローカル起動 (Dockerを使わない場合)

npx nx serve frontend

# Nxコマンドでバックエンドをローカル起動 (Dockerを使わない場合)

(cd apps/backend && source .venv/bin/activate && npx nx serve backend)

# Nxコマンドでテストを実行

npx nx test frontend

npx nx test backend

# Dockerコンテナのログを確認

docker compose logs -f

# サービスを停止

docker compose down
