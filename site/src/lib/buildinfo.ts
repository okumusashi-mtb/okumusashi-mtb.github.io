import { execSync } from 'node:child_process';

// 公開ページから「どのソースの、どの時点のビルドか」を辿れるようにするための情報。
const REPO = 'okumusashi-mtb/okumusashi-mtb.github.io';

// CI では checkout した commit が GITHUB_SHA に入る。手元ビルドでは git から取る。
function currentCommit(): string {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

// ロケールの表記揺れを避けるため、JST の年月日時分を自前で組み立てる。
function builtAtJst(now: Date): string {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'Asia/Tokyo', hour12: false,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    }).formatToParts(now).map((x) => [x.type, x.value]),
  );
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`;
}

const commit = currentCommit();

export const buildInfo = {
  commit,
  short: commit ? commit.slice(0, 7) : 'unknown',
  builtAt: builtAtJst(new Date()),
  repo: REPO,
  repoUrl: `https://github.com/${REPO}`,
  commitUrl: commit ? `https://github.com/${REPO}/commit/${commit}` : `https://github.com/${REPO}`,
};

export { builtAtJst };
