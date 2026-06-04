# PinSeeker — Product Overview

PinSeeker is a private, invite-only automated tee time booking tool for golf courses in the Albany/Capital Region of New York. It monitors course booking windows and automatically executes reservations at the moment tee times are released, giving users a competitive edge.

## Core Workflow
1. A user logs in and schedules a "booking job" — specifying course, desired date, time window, player count, and the exact release time when the tee times open.
2. The system queues the job and fires it via Google Cloud Tasks at the right moment.
3. A Playwright-powered automation bot runs headlessly against the course's booking website and completes the reservation.
4. The job status (PENDING → RUNNING → SUCCESS/FAILED) is tracked in Firestore and visible to the user in real time.

## Supported Courses
Capital Hills, Eagle Crest, Fairways of Halfmoon, Old Post Road, Orchard Creek, Saratoga Spa, Schenectady Muni, Stadium Golf Club, Town of Colonie, Van Patten.

## Key Constraints
- Access is restricted — no public registration, users are provisioned manually.
- Bookings are fire-and-forget; the bot must handle anti-bot measures (stealth mode, Tailscale exit node routing).
- `dry_run=True` mode exists for all booking functions — it executes the full flow but skips the final confirmation click. Always use it for testing.
