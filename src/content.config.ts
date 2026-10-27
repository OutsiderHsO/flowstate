import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Articles live in src/content/journal/<lang>/<slug>.md
 * The folder name is the language, so the route can be derived without
 * duplicating it in frontmatter.
 */
const journal = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/journal' }),
  schema: z.object({
    title: z.string(),
    /** One-sentence dek shown under the title. */
    dek: z.string(),
    /** ISO date */
    published: z.coerce.date(),
    updated: z.coerce.date().optional(),
    category: z.enum(['culture', 'modification', 'driving', 'review', 'essay']),
    tags: z.array(z.string()).default([]),
    /** Hero image path under /public. Local only — no hotlinking. */
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    /** Featured on the homepage cover slot. */
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
    /** Pairs the zh/en versions of the same article, for the language switch. */
    translationKey: z.string(),
  }),
});

export const collections = { journal };
