# gambitParlay — iOS app shell (Capacitor)

This wraps the deployed web app (Phase 2) in a native iOS shell using
Capacitor. It does **not** bundle a static build of the site — it points a
native WebView at your live Vercel deployment (see `server.url` in
`capacitor.config.ts`), the same content everyone sees in a browser. That's
the right call here because the site fetches fresh ratings/fixtures on every
request; a static export would go stale.

This directory is **prep only**. Nobody has submitted anything to the App
Store, and no Apple account has been touched. Everything below that requires
Xcode or an Apple Developer account is a step for you to run yourself on a
Mac — this container is Linux and can't build or sign an iOS app.

## What's already done here

- `capacitor.config.ts` — app id `com.gambitparlay.app`, app name
  "gambitParlay", pointed at a placeholder production URL.
- `ios/` — a real, generated Xcode project (`cap add ios` was run and
  succeeded in this environment, since generating the project skeleton
  doesn't require Xcode — only building and signing does).
- `www/index.html` — a minimal fallback shown only if the app can't reach
  the network on launch.

## What you need to do yourself, in order

1. **Deploy Phase 2 first** (see the root `DEPLOYMENT.md`). You need a real
   `https://...vercel.app` (or custom domain) URL before this is useful.

2. **Set the production URL.** Open `capacitor.config.ts` and replace
   `PRODUCTION_URL` with your actual deployed frontend URL.

3. **On a Mac, with Xcode installed:**
   ```bash
   cd mobile
   npm install
   npx cap sync ios
   npx cap open ios
   ```
   The last command opens the generated project in Xcode.

4. **In Xcode:**
   - Select the `App` target → *Signing & Capabilities* → sign in with your
     Apple ID and select your team (requires the paid Apple Developer
     Program, see below).
   - Set a unique bundle identifier if `com.gambitparlay.app` is already taken
     (Xcode will tell you).
   - Build and run on a simulator or your own device to confirm it loads
     your deployed site correctly before doing anything else.

5. **Everything from here on is yours to do** — this is intentionally where
   automated prep stops:
   - **Apple Developer Program enrollment** — $99/year, at
     [developer.apple.com/programs](https://developer.apple.com/programs/).
     Required before you can submit anything.
   - **App Store Connect listing** — app name, category (likely *Sports* or
     *Utilities*), description, keywords, support URL, marketing URL.
   - **Screenshots** — required for each supported device size. Capture
     these from the running app once it's pointed at your live site.
   - **Privacy policy page** — required by App Store Connect even for
     data-light apps. See the section below for what it needs to say given
     what this app actually does.
   - **App Review submission** — see the risk section below before you
     submit.

## App Review: the gambling-adjacent risk

This is a stats/analytics tool, not a sportsbook — **it doesn't take bets,
doesn't move money, and doesn't integrate with any betting operator.** That
distinction is the main thing Apple's review team will be checking for, and
it's also the main way an app like this gets rejected if the copy or UI
blur the line. Concretely, before submitting:

- **Never use language that implies placing a bet.** "Evaluate this bet",
  "stake", "edge", and "Kelly" (all already used in the product, in a
  clearly analytical framing) are fine. Avoid anything that reads like a
  call to action to bet real money — no "Bet now", no "Place bet", no
  checkout-style flow.
  - Both the fixtures cards, the backtest banner and the evaluator already
    include a "statistical model, not a guarantee" line and a "doesn't take
    bets or handle money" line — keep those visible, don't bury them in a
    footer only.
- **No odds-taking, no payment flow, no linked sportsbook.** The app never
  should collect a bankroll amount, never process a payment, and never
  hands off to a betting site's checkout. Users type in odds they saw
  elsewhere purely to run the math — nothing is submitted anywhere as a
  wager.
- **Age gating.** Apple's guideline 1.4.3 treats gambling-*adjacent* content
  (including odds/betting-strategy tools) similarly to gambling for age
  rating purposes even without real-money wagering. Set the App Store
  Connect age rating questionnaire honestly — expect this to land at 17+
  given "Simulated Gambling" / "Contests" style questions reference odds
  and stakes, even purely informational. Getting this right up front avoids
  a review bounce.
  - Check the **Gambling** section of the age-rating questionnaire
    specifically — depending on how Apple currently phrases it, a tool that
    computes betting edge from user-entered odds may need you to answer
    "yes" to a "simulated gambling" or "contests with real-money" style
    question even though no money moves. Answer based on what the app
    actually does, not what you'd prefer the rating to be — a mismatch
    between your answers and actual behavior is a rejection risk in itself.
- **Region restrictions.** Some regions require a gambling license even for
  odds-comparison tools with no money handling. If Apple's review flags a
  specific territory, the fastest fix is usually excluding that territory
  in App Store Connect's availability settings rather than contesting it.
- **Jurisdiction disclaimer.** Consider adding a line to the privacy
  policy / about page noting the app provides statistical analysis only and
  users are responsible for complying with their local laws regarding
  sports betting — this is a reasonable-diligence step, not a legal
  requirement.

## Privacy policy — what it needs to cover

Given the app (as built) doesn't create accounts, doesn't collect payment
info, and doesn't track users beyond what Vercel/your host logs by default,
the policy can be short and honest. It should state:

- **What data is collected**: none directly from the user. The app doesn't
  require sign-in, doesn't collect name/email/payment details, and doesn't
  store the odds or bet-evaluator inputs a user types in — that math runs
  client-side against the API per-request and nothing is persisted server
  side tied to a user or device.
- **Standard infrastructure logs**: your hosting providers (Vercel, and
  Render/Fly.io for the API) log request metadata (IP address, timestamp,
  requested path) for operational/security purposes, as essentially all web
  hosts do. Name them plainly rather than omitting this.
- **No third-party analytics or ad SDKs** — true as shipped; if you add
  analytics later (e.g. Vercel Analytics, Plausible), update the policy
  before you ship that change, not after.
- **No age-restricted data collection** — the app doesn't ask a user's age;
  age-gating (if any) happens at the App Store distribution level.
- **Contact information** — an email address or contact page for privacy
  questions (Apple requires a live link, not just a paragraph in-app).

A single static page hosted at e.g. `/privacy` on the Next.js frontend
satisfies this — Apple requires a URL in App Store Connect, not just an
in-app screen. This has not been built yet; it's a small addition to
`src/app/privacy/page.tsx` once you're ready to write the final copy
(a template based on the bullets above can be dropped in fast).
