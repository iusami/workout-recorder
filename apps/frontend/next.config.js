//@ts-check

// eslint-disable-next-line @typescript-eslint/no-var-requires
const { composePlugins, withNx } = require('@nx/next');

/**
 * @type {import('@nx/next/plugins/with-nx').WithNxOptions}
 **/
const nextConfig = {
  // Use this to set Nx-specific options
  // See: https://nx.dev/recipes/next/next-config-setup
  nx: {
    // Nx の非推奨 SVGR サポートを無効化
    svgr: false,
  },
  output: 'standalone', // Next.js 13+ のスタンドアロンビルドを使用

  // Webpack設定を追加してSVGRを手動で設定
  webpack(config, { isServer }) {
    // 既存のSVGローダーを見つける
    const fileLoaderRule = config.module.rules.find((rule) =>
      rule.test?.test?.('.svg')
    );

    config.module.rules.push(
      // SVGR ローダーを追加: JS/TS ファイルからインポートされたSVGを処理
      {
        test: /\.svg$/i,
        issuer: /\.[jt]sx?$/, // .js, .jsx, .ts, .tsx ファイルからのインポートに限定
        resourceQuery: { not: /url/ }, // ?url がついていない場合に適用
        use: ['@svgr/webpack'],
      },
      // 既存のローダーを修正: ?url がついている場合のみ処理するように
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // ?url がついている場合に適用
      }
    );

    // 元のローダーが全てのSVGを処理しないように除外設定を追加
    fileLoaderRule.exclude = /\.svg$/i;

    return config;
  },
};

const plugins = [
  // Add more Next.js plugins to this list if needed.
  withNx,
];

module.exports = composePlugins(...plugins)(nextConfig);
