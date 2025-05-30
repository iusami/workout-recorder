-- userユーザーは既にPOSTGRES_USERとして設定されているため、追加の設定は不要
-- ただし、テスト用データベースを作成し、適切な権限を設定する

-- userにスーパーユーザー権限を付与
ALTER USER "user" WITH SUPERUSER;

-- テスト用データベースを作成
CREATE DATABASE "workout-recorder-test";

-- テスト用データベースに接続して権限設定
\c "workout-recorder-test";
-- userはスーパーユーザーとして作成されているため、全権限を持つ
-- 念のため明示的に権限を設定
GRANT ALL ON SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "user";

-- 本番用データベースに戻って同様の設定
\c "workout-recorder";
-- userはデータベースオーナーなので全権限を持つが、念のため明示的に設定
GRANT ALL ON SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "user";

-- 将来のテーブル作成時にもuserが所有者になるように設定
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT ALL ON TABLES TO "user";
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT ALL ON SEQUENCES TO "user";

-- "user"ロールがpublicスキーマに作成するオブジェクトのデフォルト権限を設定
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT ALL ON TABLES TO "user";
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT ALL ON SEQUENCES TO "user";
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO "user";
ALTER DEFAULT PRIVILEGES FOR ROLE "user" IN SCHEMA public GRANT USAGE ON TYPES TO "user";


-- publicスキーマ自体の権限も確認
GRANT USAGE ON SCHEMA public TO "user";
GRANT CREATE ON SCHEMA public TO "user";


-- Alembicのバージョン管理テーブルに対する権限設定
-- テーブルが存在する場合のみ実行
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version' AND table_schema = 'public') THEN
        ALTER TABLE public.alembic_version OWNER TO "user";
        GRANT ALL PRIVILEGES ON TABLE public.alembic_version TO "user";
    END IF;
END $$;
