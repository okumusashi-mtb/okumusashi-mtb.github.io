import { describe, it, expect } from 'vitest';
import { builtAtJst, buildInfo } from './buildinfo';

describe('buildinfo', () => {
  it('UTC を JST の年月日時分に直す', () => {
    // 2026-08-17T15:00:00Z = 2026-08-18 00:00 JST (日付が繰り上がる)
    expect(builtAtJst(new Date('2026-08-17T15:00:00Z'))).toBe('2026-08-18 00:00');
  });

  it('ゼロ埋めした固定長で返す', () => {
    expect(builtAtJst(new Date('2026-01-02T00:04:00Z'))).toBe('2026-01-02 09:04');
  });

  it('コミットへのリンクを組み立てる', () => {
    expect(buildInfo.commitUrl.startsWith(buildInfo.repoUrl)).toBe(true);
    expect(buildInfo.short.length).toBeLessThanOrEqual(7);
  });
});
