type LangKey = 'zh' | 'en';

type Dict = {
  nav: { home: string; automotive: string; fiction: string; about: string; langSwitch: string };
  sections: {
    featured: string;
    latest: string;
    categories: string;
    index: string;
    colophon: string;
  };
  labels: {
    readMore: string;
    minRead: string;
    words: string;
    updated: string;
    issue: string;
    filterAll: string;
    empty: string;
    draft: string;
    backToList: string;
    contents: string;
    translationMissing: string;
    readIn: string;
    chapterOf: string;
  };
  footer: {
    builtWith: string;
    rights: string;
    placeholderNote: string;
  };
  fiction: {
    shelf: string;
    fandom: string;
    original: string;
    wordCount: string;
    /** Shown on fan works — non-commercial disclaimer. */
    disclaimer: string;
    disclaimerShort: string;
    rating: string;
    ratingNote: Record<'G' | 'T' | 'M' | 'E', string>;
    status: { ongoing: string; complete: string };
    noTranslation: string;
  };
};

export const t: Record<LangKey, Dict> = {
  zh: {
    nav: {
      home: '首页',
      automotive: '汽车',
      fiction: '文学',
      about: '关于',
      langSwitch: '切换语言',
    },
    sections: {
      featured: '封面',
      latest: '最新',
      categories: '栏目',
      index: '全部',
      colophon: '关于本站',
    },
    labels: {
      readMore: '阅读',
      minRead: '分钟',
      words: '字',
      updated: '更新于',
      issue: '期号',
      filterAll: '全部',
      empty: '暂无内容。',
      draft: '草稿',
      backToList: '返回列表',
      contents: '目录',
      translationMissing: '暂无译文',
      readIn: '其他语言',
      chapterOf: '所属',
    },
    footer: {
      builtWith: '由 Astro 静态生成',
      rights: '版权所有',
      placeholderNote: '本站示例内容为占位文本，非真实测评。',
    },
    fiction: {
      shelf: '书架',
      fandom: '同人',
      original: '原创',
      wordCount: '字数',
      disclaimer:
        '本文为同人创作，非商业用途。所涉原作角色与世界观之著作权归原作者及权利方所有，本作品不主张其所有权，亦不代表原作官方立场。',
      disclaimerShort: '同人创作 · 非商业 · 角色版权归原作者',
      rating: '分级',
      ratingNote: {
        G: '全年龄',
        T: '建议 13 岁以上',
        M: '建议 17 岁以上',
        E: '仅限成人',
      },
      status: { ongoing: '连载中', complete: '已完结' },
      noTranslation: '这篇暂时只有中文版本。',
    },
  },
  en: {
    nav: {
      home: 'Home',
      automotive: 'Cars',
      fiction: 'Fiction',
      about: 'About',
      langSwitch: 'Change language',
    },
    sections: {
      featured: 'Featured',
      latest: 'Latest',
      categories: 'Sections',
      index: 'All',
      colophon: 'Colophon',
    },
    labels: {
      readMore: 'Read',
      minRead: 'min read',
      words: 'words',
      updated: 'Updated',
      issue: 'Issue',
      filterAll: 'All',
      empty: 'Nothing here yet.',
      draft: 'Draft',
      backToList: 'Back to list',
      contents: 'Contents',
      translationMissing: 'No translation yet',
      readIn: 'Other languages',
      chapterOf: 'Part of',
    },
    footer: {
      builtWith: 'Statically generated with Astro',
      rights: 'All rights reserved',
      placeholderNote: 'Sample content is placeholder text — not a real review.',
    },
    fiction: {
      shelf: 'Shelf',
      fandom: 'Fan work',
      original: 'Original',
      wordCount: 'words',
      disclaimer:
        'This is fan fiction, non-commercial. All characters and settings belong to their original creators and rights holders. No ownership is claimed and no official affiliation is implied.',
      disclaimerShort: 'Fan work · non-commercial · characters © original creators',
      rating: 'Rating',
      ratingNote: {
        G: 'General audiences',
        T: 'Teen and up',
        M: 'Mature',
        E: 'Explicit',
      },
      status: { ongoing: 'Ongoing', complete: 'Complete' },
      noTranslation: 'This piece is currently only available in English.',
    },
  },
};

/** Automotive category slugs; display names differ per language. */
export const CATEGORIES = {
  culture: { zh: '汽车文化', en: 'Car Culture' },
  modification: { zh: '改装研究', en: 'Modification' },
  driving: { zh: '驾驶体验', en: 'Driving' },
  review: { zh: '车辆测评', en: 'Reviews' },
  essay: { zh: '随笔', en: 'Essays' },
} as const;

export type CategoryKey = keyof typeof CATEGORIES;

/** Fiction genres (more useful than car categories on a story shelf). */
export const GENRES = {
  fanfiction: { zh: '同人文', en: 'Fan Fiction' },
  shortstory: { zh: '短篇小说', en: 'Short Story' },
  flash: { zh: '微型小说', en: 'Flash Fiction' },
  serial: { zh: '连载', en: 'Serial' },
} as const;

export type GenreKey = keyof typeof GENRES;
