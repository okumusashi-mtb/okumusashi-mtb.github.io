// Cloudflare Web Analytics のビーコン設定。
//
// このトークンは秘密情報ではない。配信される HTML にそのまま載るもので、
// Cloudflare 側も公開前提で発行している。したがってリポジトリに直接書いてよい。
//
// 取得場所: Cloudflare ダッシュボード > Analytics & Logs > Web Analytics
//           サイトを追加すると発行される JS snippet の data-cf-beacon の token。
//
// 空文字にすればビーコンは出力されない。計測をやめるときはここを空にする。
//
// 本番は GitHub Pages なので、Cloudflare Pages 側のダッシュボードから自動挿入する
// 方式は使えない (pages.dev にしか効かない)。そのため <head> ではなく自前で
// Base.astro の </body> 直前に出している。
export const cfBeaconToken = '5700042ebdf74cf9b55bf64bacdd3d9b';

// Cookie を使わず個人を追跡しないため、同意バナーは不要。
// https://developers.cloudflare.com/web-analytics/
