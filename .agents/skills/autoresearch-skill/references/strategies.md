# Optimization Strategies by Target Type

Reference guide for the autoresearch loop. Strategies are ordered by expected impact within each category. Try high-impact strategies first.

---

## Test Speed (pytest)

| # | Strategy | What to change | Expected impact | Risk |
|---|----------|---------------|-----------------|------|
| 1 | **Add pytest-xdist parallelization** | Install pytest-xdist, add `-n auto` to pytest config or invocation | 2-5x speedup on multi-core machines | Medium -- tests must be independent (no shared state between test files) |
| 2 | **Widen fixture scope** | Change `@pytest.fixture(scope="function")` to `scope="session"` or `scope="module"` for expensive fixtures (DB setup, API clients, large data) | 20-60% reduction if fixtures dominate runtime | Medium -- session fixtures are shared, must not mutate state |
| 3 | **Replace real I/O with mocks** | Replace filesystem, network, or DB calls in unit tests with `unittest.mock.patch` or `pytest-mock` | 10-40% per test that hits I/O | Low -- only for unit tests, never integration |
| 4 | **Remove unnecessary setup/teardown** | Remove `setUp`/`tearDown` or fixture work that tests don't actually need | 5-20% | Low |
| 5 | **Consolidate duplicate fixtures** | Merge identical or near-identical fixtures defined in multiple conftest.py files | 5-15% from reduced fixture initialization | Low |
| 6 | **Use `--tb=no` or `--tb=line` in metric command** | Reduce traceback verbosity in non-interactive runs | 2-5% (less output processing) | None |
| 7 | **Lazy imports in test files** | Move heavy imports inside test functions that use them, not at module top-level | 5-15% from reduced import time | Low |
| 8 | **Skip slow tests with markers** | Add `@pytest.mark.slow` and exclude from default runs | Varies -- removes slowest tests from default suite | Medium -- must ensure marked tests still run somewhere |
| 9 | **Use `pytest-randomly` seed pinning** | Pin random seed to avoid test order flakiness, enabling safer parallelization | Indirect -- enables xdist | None |
| 10 | **Profile first** | Run `pytest --durations=20` to find the 20 slowest tests before optimizing | No direct speedup but guides strategy selection | None |

---

## Bundle Size (JavaScript/TypeScript)

| # | Strategy | What to change | Expected impact | Risk |
|---|----------|---------------|-----------------|------|
| 1 | **Tree-shake unused exports** | Ensure `sideEffects: false` in package.json, check imports are specific (`import { x }` not `import *`) | 10-30% | Low |
| 2 | **Code-split routes** | Add dynamic `import()` for route-level components | 20-50% initial bundle reduction | Low -- adds loading states |
| 3 | **Replace heavy dependencies** | Swap moment.js with dayjs, lodash with lodash-es or native, etc. | 10-40% per swapped library | Medium -- API differences |
| 4 | **Enable compression** | Add gzip/brotli compression in build pipeline | 60-80% transfer size reduction | None |
| 5 | **Analyze with bundle visualizer** | Run `npx webpack-bundle-analyzer` or `next build --analyze` to find largest chunks | No direct reduction but guides strategy | None |
| 6 | **Remove unused CSS** | Add PurgeCSS or Tailwind's built-in purging | 5-30% of CSS size | Low |
| 7 | **Optimize images** | Convert to WebP/AVIF, add lazy loading | Varies per image count | Low |

---

## Build Time

| # | Strategy | What to change | Expected impact | Risk |
|---|----------|---------------|-----------------|------|
| 1 | **Enable build caching** | Configure persistent cache (Webpack cache, Next.js SWC cache, Turborepo) | 40-80% on subsequent builds | None |
| 2 | **Parallelize compilation** | Use `thread-loader` (Webpack) or ensure SWC/esbuild is the compiler | 20-50% | Low |
| 3 | **Reduce TypeScript strictness for build** | Use `skipLibCheck: true` in tsconfig | 10-30% on type checking | Low |
| 4 | **Minimize file watching scope** | Add ignore patterns for node_modules, dist, .git | 5-15% on watch mode | None |
| 5 | **Use faster alternatives** | Vite instead of Webpack, SWC instead of Babel, esbuild for scripts | 2-10x for full migration | High -- significant migration |

---

## API Latency

| # | Strategy | What to change | Expected impact | Risk |
|---|----------|---------------|-----------------|------|
| 1 | **Add caching layer** | Redis/memcached for repeated queries, HTTP cache headers | 50-90% for cache hits | Medium -- cache invalidation complexity |
| 2 | **Parallelize independent calls** | `asyncio.gather()` or `Promise.all()` for independent operations | 20-60% when operations were sequential | Low |
| 3 | **Add database indexes** | Index columns used in WHERE, JOIN, ORDER BY | 10-100x for specific queries | Low -- small write overhead |
| 4 | **Reduce payload size** | Return only needed fields, paginate, compress responses | 10-30% transfer time | Low |
| 5 | **Connection pooling** | Reuse DB/HTTP connections instead of per-request creation | 10-40% | Low |
| 6 | **Optimize N+1 queries** | Use eager loading, batch queries, or dataloaders | 50-90% for N+1 patterns | Medium |

---

## Prompt Quality (LLM prompts)

| # | Strategy | What to change | Expected impact | Risk |
|---|----------|---------------|-----------------|------|
| 1 | **Add output contract** | Define exact expected output format in the prompt | 20-40% format compliance improvement | None |
| 2 | **Add examples** | 2-3 few-shot examples of ideal input/output pairs | 15-30% quality improvement | Low -- increases token count |
| 3 | **Simplify instructions** | Remove redundant or conflicting instructions | 5-15% (reduces confusion) | Low |
| 4 | **Add verification step** | "Before responding, verify that..." at the end | 10-20% accuracy improvement | Low -- slight latency increase |
| 5 | **Restructure for clarity** | Use headers, numbered lists, XML tags to separate concerns | 10-25% | None |
| 6 | **Remove filler** | Delete hedge words, preamble, unnecessary context | 5-10% (reduced token count, clearer signal) | None |

---

## General Principles

When the loop stalls (5 consecutive discards), try:

1. **Change strategy category** -- if all fixture changes are exhausted, try parallelization
2. **Profile before guessing** -- run profiling tools to find the actual bottleneck
3. **Combine kept changes** -- sometimes individually neutral changes compound
4. **Widen scope** -- if the asset path is too narrow, suggest expanding it to the user
5. **Reduce metric noise** -- increase metric runs from 3 to 5 if results are borderline
