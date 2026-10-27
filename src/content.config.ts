import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Content lives in src/content/<collection>/<lang>/<slug>.md
 * The folder name is the language, so routes are derived without
 * duplicating it in frontmatter.
 */

// ---------------------------------------------------------------- automotive
const automotive = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/automotive' }),
  schema: z.object({
    title: z.string(),
    dek: z.string(),
    published: z.coerce.date(),
    updated: z.coerce.date().optional(),
    category: z.enum(['culture', 'modification', 'driving', 'review', 'essay']),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
    translationKey: z.string(),
  }),
});

// ------------------------------------------------------------------- fiction
const fiction = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/fiction' }),
  schema: z.object({
    title: z.string(),
    /** Logline / one-line hook. */
    dek: z.string(),
    published: z.coerce.date(),
    updated: z.coerce.date().optional(),
    genre: z.enum(['fanfiction', 'shortstory', 'flash', 'serial']),
    /** "fanfiction" triggers the non-commercial disclaimer block. */
    nature: z.enum(['fanwork', 'original']).default('original'),
    /** Source work for fan fiction, e.g. an anime/game title. */
    fandom: z.string().optional(),
    /** Content rating, shown as a badge. */
    rating: z.enum(['G', 'T', 'M', 'E']).default('G'),
    status: z.enum(['complete', 'ongoing']).default('complete'),
    /** Multi-part stories sharing a series title group together. */
    series: z.string().optional(),
    /**
     * Position within the series. Deliberately a float, not an int: authors
     * commonly slot an interlude between 12 and 13 as "12.5".
     */
    part: z.number().nonnegative().optional(),
    tags: z.array(z.string()).default([]),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
    /** Pairs translations. Optional: a story may exist in one language only. */
    translationKey: z.string().optional(),
  }),
});

export const collections = { automotive, fiction };
