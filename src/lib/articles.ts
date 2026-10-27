import { getCollection, type CollectionEntry } from 'astro:content';
import type { Lang } from './site';

export type AutomotiveEntry = CollectionEntry<'automotive'>;
export type FictionEntry = CollectionEntry<'fiction'>;
export type AnyEntry = AutomotiveEntry | FictionEntry;

/** The glob loader ids files as "<lang>/<slug>" (no extension). */
export function splitId(id: string): { lang: string; slug: string } {
  const [lang, ...rest] = id.split('/');
  return { lang, slug: rest.join('/') };
}

export function entryLang(entry: AnyEntry): string {
  return splitId(entry.id).lang;
}

export function entrySlug(entry: AnyEntry): string {
  return splitId(entry.id).slug;
}

export const entryHref = (entry: AnyEntry, section: 'automotive' | 'fiction') =>
  `/${entryLang(entry)}/${section}/${entrySlug(entry)}/`;

// ------------------------------------------------------------- automotive
const byDateDesc = (a: AnyEntry, b: AnyEntry) =>
  b.data.published.getTime() - a.data.published.getTime();

export async function getAutomotive(lang: Lang): Promise<AutomotiveEntry[]> {
  const all = await getCollection('automotive', ({ data }) => !data.draft);
  return all.filter((e) => entryLang(e) === lang).sort(byDateDesc);
}

export async function getLeadAutomotive(lang: Lang): Promise<AutomotiveEntry | undefined> {
  const list = await getAutomotive(lang);
  return (
    list.find((e) => e.data.featured && e.data.image) ??
    list.find((e) => e.data.image) ??
    list[0]
  );
}

// ---------------------------------------------------------------- fiction
/**
 * Stories for one language, ordered for a shelf.
 *
 * Plain date ordering is wrong for serials: every chapter shares the same
 * publish date, so they come out scrambled. Sort by (series, part) first,
 * keeping different works grouped, then newest-first across works.
 */
export async function getFiction(lang: Lang): Promise<FictionEntry[]> {
  const all = await getCollection('fiction', ({ data }) => !data.draft);
  const mine = all.filter((e) => entryLang(e) === lang);

  const seriesFirst = new Map<string, number>();
  for (const e of mine) {
    const s = e.data.series;
    if (s && !seriesFirst.has(s)) {
      seriesFirst.set(s, e.data.published.getTime());
    }
  }

  return mine.sort((a, b) => {
    const sa = a.data.series;
    const sb = b.data.series;

    // Serials are the deepest works on a shelf; lead with them.
    if (sa && !sb) return -1;
    if (!sa && sb) return 1;

    // Standalone works come before serials, newest first.
    if (!sa && !sb) {
      // An explicitly featured piece still wins among standalones.
      if (a.data.featured !== b.data.featured) return a.data.featured ? -1 : 1;
      return byDateDesc(a, b);
    }

    // Different serials: newest series first.
    if (sa !== sb) {
      return (seriesFirst.get(sb) ?? 0) - (seriesFirst.get(sa) ?? 0);
    }

    // Same serial: follow the chapter order.
    const pa = a.data.part ?? 0;
    const pb = b.data.part ?? 0;
    if (pa !== pb) return pa - pb;
    return byDateDesc(a, b);
  });
}

export async function getLeadFiction(lang: Lang): Promise<FictionEntry | undefined> {
  const list = await getFiction(lang);
  return list.find((e) => e.data.featured) ?? list[0];
}

/**
 * Whether any fiction exists in a language. The nav dims the Fiction link
 * when a visitor's language has nothing to read yet.
 */
export async function hasFiction(lang: Lang): Promise<boolean> {
  return (await getFiction(lang)).length > 0;
}

// ------------------------------------------------------- cross-language
/**
 * Find the counterpart of an entry in another language.
 * Returns the list page when no translation exists — a story may be
 * published in one language only.
 */
export async function getTranslationTarget(
  entry: AnyEntry,
  collection: 'automotive' | 'fiction',
  lang: Lang,
): Promise<string> {
  const key = entry.data.translationKey;
  if (key) {
    const all =
      collection === 'automotive'
        ? await getCollection('automotive')
        : await getCollection('fiction');
    const match = all.find(
      (e) => entryLang(e) === lang && e.data.translationKey === key && !e.data.draft,
    );
    if (match) return entryHref(match as AnyEntry, collection);
  }
  return `/${lang}/${collection === 'automotive' ? 'automotive' : 'fiction'}/`;
}

// ------------------------------------------------------------------ utils
/** Rough reading time. CJK per character, latin per word. */
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

/** Word/character count used on the fiction shelf. */
export function wordCount(body: string, lang: Lang): number {
  if (!body) return 0;
  if (lang === 'zh') {
    return (body.match(/[\u4e00-\u9fff]/g) ?? []).length;
  }
  return (body.match(/[A-Za-z0-9'’-]+/g) ?? []).length;
}

export function formatCount(n: number): string {
  if (n >= 10000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
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

/** Markdown → short plain-text teaser. */
export function excerpt(body: string, max = 200): string {
  const paragraphs = body
    .replace(/^---[\s\S]*?---/, '')
    .replace(/```[\s\S]*?```/g, '')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter((p) => p && !/^(#|>|\||!\[|[-*+]\s|\d+\.\s|---)/.test(p));

  const clean = (paragraphs[0] ?? '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (clean.length <= max) return clean;
  const cut = clean.slice(0, max);
  const lastSpace = cut.lastIndexOf(' ');
  return `${(lastSpace > max * 0.6 ? cut.slice(0, lastSpace) : cut).trimEnd()}…`;
}
