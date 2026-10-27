import { getCollection, type CollectionEntry } from 'astro:content';
import type { Lang } from './site';

export type Article = CollectionEntry<'journal'>;

/** The glob loader ids files as "<lang>/<slug>" (no extension). */
export function splitId(id: string): { lang: string; slug: string } {
  const [lang, ...rest] = id.split('/');
  return { lang, slug: rest.join('/') };
}

export function articleLang(entry: Article): string {
  return splitId(entry.id).lang;
}

export function articleSlug(entry: Article): string {
  return splitId(entry.id).slug;
}

export const articleHref = (entry: Article) =>
  `/${articleLang(entry)}/journal/${articleSlug(entry)}/`;

function byDateDesc(a: Article, b: Article) {
  return b.data.published.getTime() - a.data.published.getTime();
}

/** Published articles for one language, newest first. */
export async function getArticles(lang: Lang): Promise<Article[]> {
  const all = await getCollection('journal', ({ data }) => !data.draft);
  return all.filter((e) => articleLang(e) === lang).sort(byDateDesc);
}

/** The featured article, or the newest one as a fallback. */
export async function getLead(lang: Lang): Promise<Article | undefined> {
  const list = await getArticles(lang);
  return list.find((e) => e.data.featured && e.data.image) ?? list.find((e) => e.data.image) ?? list[0];
}

/**
 * Find the counterpart of an article in the other language.
 * Falls back to that language's journal index when no translation exists.
 */
export async function getTranslationTarget(entry: Article, lang: Lang): Promise<string> {
  const all = await getCollection('journal');
  const match = all.find(
    (e) => articleLang(e) === lang && e.data.translationKey === entry.data.translationKey,
  );
  return match ? articleHref(match) : `/${lang}/journal/`;
}

/** Rough reading time. CJK is counted per character, latin per word. */
export function readingTime(body: string, lang: Lang): number {
  if (!body) return 1;
  if (lang === 'zh') {
    const cjk = (body.match(/[\u4e00-\u9fff]/g) ?? []).length;
    const latin = (body.replace(/[\u4e00-\u9fff]/g, ' ').match(/[A-Za-z0-9]+/g) ?? []).length;
    return Math.max(1, Math.round((cjk + latin * 1.6) / 400));
  }
  const words = (body.match(/[A-Za-z0-9'’-]+/g) ?? []).length;
  return Math.max(1, Math.round(words / 220));
}

export function formatDate(date: Date, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === 'zh' ? 'zh-CN' : 'en-GB', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'UTC',
  })
    .format(date)
    .replace(/\//g, '.');
}
