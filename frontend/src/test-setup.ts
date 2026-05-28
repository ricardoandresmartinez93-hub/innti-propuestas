/**
 * Global test setup file — runs before every test file.
 *
 * Handles three categories of noise that appear in every test run without
 * affecting test correctness:
 *
 * 1. React Router v6 → v7 future-flag warnings: informational only, not
 *    actionable inside unit tests (the flags belong on the app's <BrowserRouter>
 *    in production code, not on the <MemoryRouter> wrappers used in tests).
 *
 * 2. jsdom "Not implemented: navigation" errors: jsdom cannot perform real
 *    browser navigation. File-download code creates a temporary <a> element,
 *    sets href to a blob URL, and calls .click(). That click triggers jsdom's
 *    navigation path, which always throws. Overriding the prototype prevents it.
 *
 * 3. React "Function components cannot be given refs" warning: suppressed here
 *    as a safety net; the primary fix is in ProposalDetailPage.test.tsx where
 *    the ProposalEditor mock now uses React.forwardRef.
 */

// --- 1. Suppress React Router v6 → v7 future-flag warnings ----------------
const _originalWarn = console.warn.bind(console)
console.warn = (...args: unknown[]) => {
  const msg = typeof args[0] === 'string' ? args[0] : ''
  if (msg.includes('React Router Future Flag Warning')) return
  _originalWarn(...args)
}

// --- 2. Prevent jsdom navigation errors from anchor .click() calls ---------
// File-download handlers create a hidden <a href="blob:..."> and call .click().
// jsdom cannot navigate to blob URLs and throws "Not implemented: navigation".
// Replacing the method with a no-op keeps the test assertions intact while
// silencing the error.
HTMLAnchorElement.prototype.click = function () { /* noop in jsdom */ }

// --- 3. Safety-net: filter the forwardRef console.error --------------------
// The root fix is the forwardRef mock in ProposalDetailPage.test.tsx.
// This guard handles any remaining occurrences from third-party components.
const _originalError = console.error.bind(console)
console.error = (...args: unknown[]) => {
  const msg = typeof args[0] === 'string' ? args[0] : ''
  if (msg.includes('Function components cannot be given refs')) return
  _originalError(...args)
}
