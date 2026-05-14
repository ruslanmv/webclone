# Download-Resistance Security Testing

WebClone includes internal **content exfiltration / download-resistance** audit commands for applications you own or are authorized to test. The goal is to verify server-side entitlement controls, minimal delivery, cache safety, and traceability—not to bypass copy protection or export a protected data set.


## JavaScript-rendered downloads

The normal crawler uses raw HTTP by default. To save an authorized JavaScript-rendered preview, use `clone --render-js` with a Selenium cookie file:

```bash
webclone clone "https://fictional-audit.invalid/exam/MOON-PORTAL-7" \
  --cookie-file ./cookies/paid.json \
  --render-js \
  --render-wait 3 \
  --max-pages 1
```

Use this only for content you own or are authorized to archive. For leak testing, prefer `webclone audit --render-js` because it records sanitized counts and marker names instead of copying all rendered content into the report.

## Safer single-profile audit

Use `webclone audit` when you want to test one role/profile against one exam URL:

```bash
webclone audit "https://fictional-audit.invalid/exam/MOON-PORTAL-7" \
  --profile free_user \
  --cookie-file ./cookies/free.json \
  --report ./reports/free-user-report.json
```

For JavaScript-driven previews, add `--render-js`. This opens the page with Selenium, waits for client-side rendering, and records sanitized evidence such as visible/received counts, matched sensitive marker names, storage marker names, cache names, and watermark markers. It does **not** write copied protected records into the report.

```bash
webclone audit "https://fictional-audit.invalid/exam/MOON-PORTAL-7" \
  --profile paid_user \
  --cookie-file ./cookies/paid.json \
  --render-js \
  --watermark-pattern "synthetic-user@example.invalid" \
  --report ./reports/paid-rendered-report.json
```

If your owned staging app exposes an authorized test-export/audit path, pass a signed token. WebClone sends it as both `Authorization: Bearer ...` and `X-WebClone-Test-Export-Token`; the server remains responsible for deciding what that role may access.

```bash
webclone audit "https://fictional-audit.invalid/exam/MOON-PORTAL-7" \
  --profile paid_user \
  --auth-token "$TEST_EXPORT_TOKEN" \
  --report ./reports/test-export-report.json
```

## Full role matrix suite

Use `webclone security-test` to test all standard entitlement roles:

```bash
webclone security-test "https://fictional-audit.invalid" MOON-PORTAL-7 \
  --role-cookie free=./cookies/free.json \
  --role-cookie paid=./cookies/paid.json \
  --role-cookie expired=./cookies/expired.json \
  --role-cookie suspended=./cookies/suspended.json \
  --role-cookie admin=./cookies/admin.json \
  --render-js \
  --route-template "/nebula/{resource_id}" \
  --route-template "/api/lunar-vault/{resource_id}/manifest" \
  --output ./reports/security_report.json
```

Anonymous requests are always tested without cookies. Any role without a `--role-cookie` mapping is tested as an unauthenticated request, which is useful while building the account matrix incrementally.

## HAR/API audit

Use `webclone audit-har` with a browser DevTools HAR export from an authorized test session to discover JSON/API overexposure that may not appear in initial HTML:

```bash
webclone audit-har ./paid-session.har \
  --expected-role paid_user \
  --report ./reports/network-leak-report.json
```

The HAR audit identifies sensitive API/export/print/download endpoints, matched sensitive marker names, overlarge JSON collections, and risky cache headers without storing response bodies in the report.

## Test modes

The runner has four modes:

1. `role-access` checks sensitive protected-page and API routes for each role.
2. `content-leak` searches HTML/API responses for hidden question-bank, answer, explanation, and protected-content markers; it also checks risky cache headers and minimal delivery evidence.
3. `bulk` performs a bounded sequential page-access simulation and expects denial, challenge, or rate limiting for non-admin roles.
4. `rendered` uses Selenium for JavaScript-rendered previews and inspects localStorage, sessionStorage, IndexedDB names, service worker cache names, visible counts, hidden source markers, and watermark markers.

Run a subset with repeated `--mode` options:

```bash
webclone security-test "https://fictional-audit.invalid" MOON-PORTAL-7 --mode role-access --mode content-leak
```

## Routes covered

By default, the runner includes common protected-page route templates. For custom products, prefer `--route-template` with unreal or staging-only paths. The built-in templates are:

```text
/exam/{resource_id}
/exam/{resource_id}?page=2
/exam/{resource_id}/print
/exam/{resource_id}/download
/exam/{resource_id}/view-all
/api/exams/{resource_id}/questions
/api/exams/{resource_id}/answers
/api/exams/{resource_id}/explanations
/api/exams/{resource_id}/export
```

## Internal checklist

Use the JSON report together with this checklist before releasing protected content:

```text
[ ] Free users cannot access paid pages by URL
[ ] Expired users cannot access previously paid pages
[ ] Print/export/download endpoints require server-side authorization
[ ] Full protected data set is never sent to the browser
[ ] Answers are not embedded in hidden HTML for unauthorized users
[ ] API responses contain only authorized page data
[ ] localStorage/sessionStorage do not contain protected data sets
[ ] Service worker cache does not store exam content
[ ] Browser save-page does not preserve unauthorized hidden data
[ ] Direct object references are protected
[ ] Sequential page/API enumeration is rate-limited
[ ] Bulk access triggers alerts
[ ] Pages use private/no-store cache headers
[ ] Paid content includes user/session watermarking
```

A passing standard is: a user may only download or save the exact content they are authorized to view at that moment. They must never receive the full protected resource, answer key, explanations, print view, or export data unless their role explicitly allows it.
