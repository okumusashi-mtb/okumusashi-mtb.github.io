// フッターに並べるリンク。会の公式サイト (Wix) のページ構成は pages-sitemap.xml で
// 列挙したもので、2026-08-18 に全件 200 を確認している。
//
// Wix は過去コンテンツの削除が進んでおり、いずれページごと失われる可能性がある。
// 移転・閉鎖のときはこのファイルだけ直せば全ページのフッターが変わる。
const WIX = 'https://okumusashimtb.wixsite.com/omcweb';
const wix = (path: string) => `${WIX}/${encodeURIComponent(path)}`;

export type FooterLink = { label: string; href: string };
export type FooterGroup = { title: string; links: FooterLink[] };

export function footerGroups(base: string): FooterGroup[] {
  return [
    {
      title: 'このサイト',
      links: [
        { label: 'トップ', href: base },
        { label: '活動アーカイブ', href: `${base}activities/` },
        { label: '会について', href: `${base}about/` },
        { label: '公式ブログ', href: `${WIX}/blog` },
      ],
    },
    {
      title: '会について',
      links: [
        { label: 'あらまし', href: wix('about-us') },
        { label: '活動', href: wix('activity') },
        { label: '会則', href: wix('regulations') },
      ],
    },
    {
      title: '入会・申し込み',
      links: [
        { label: '入会方法', href: wix('membership') },
        { label: '新規入会', href: wix('newmember') },
        { label: '新規・18歳未満', href: wix('newmember-u18') },
        { label: '継続・登録内容の変更', href: wix('renewal') },
        { label: '子ども教室応募', href: wix('form-kidsschool') },
      ],
    },
    {
      title: 'よくある質問',
      links: [
        { label: '当会について', href: wix('faq-omc') },
        { label: 'じてんしゃ広場について', href: wix('faq-naguri') },
        { label: '子ども教室について', href: wix('faq-kidsschool') },
        { label: 'お問い合わせ', href: wix('inquiry') },
      ],
    },
  ];
}
