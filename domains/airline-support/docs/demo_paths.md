# Demo Paths

These scripted paths are the source of truth for the `airline-support` domain.
Schema, prompt design, generated data, and semantic-cache behavior should all
exist to support these conversations cleanly.

> Tip: Use `Context Retriever` for the main demo. For semantic-cache paths,
> repeat the exact same prompt on a fresh thread so the cache read behavior is
> visible in the trace.

## Path 1: Flagship Disruption Recovery

Opening prompt:
`My flight was disrupted. What happened?`

Follow-ups:
- `Show me my updated itinerary.`
- `Do I need to do anything next?`

Expected tool sequence:
1. `get_current_user_profile`
2. `filter_booking_by_customer_id`
3. `filter_itinerarysegment_by_booking_id`
4. `filter_operatingflight_by_operating_flight_id` using the itinerary segment's `operating_flight_id`
5. `filter_operationaldisruption_by_operating_flight_id`
6. `filter_reaccommodationrecord_by_booking_id` or `filter_reaccommodationrecord_by_customer_id`
7. `search_travelpolicydoc_by_text(value="rebooking after cancellation")` when the user asks about options or rules

Required supporting records:
- `CustomerProfile`: `AIRCUST_001`
- `Booking`: `BOOK_001` / locator `ZX73QF`
- `ItinerarySegment`: cancelled original `SEG_001` / `ZX402`
- `ItinerarySegment`: updated `SEG_002` / `ZX406`
- `OperatingFlight`: `OF_001` and `OF_002`
- `OperationalDisruption`: `OD_001`
- `ReaccommodationRecord`: `REAC_001`

Expected assistant behavior:
- Identify the signed-in traveller first.
- Explain that `ZX402` was cancelled from the operational disruption record and that the traveller is already rebooked onto `ZX406` from the reaccommodation record.
- Separate confirmed record-backed facts from general policy guidance.
- When asked for the updated itinerary, cite the rebooked flight, route, and new timing.
- When asked about next steps, use the reaccommodation record and the updated segment first, then bring in policy only as supplemental guidance.

Expected semantic-cache behavior:
- First-turn read attempt may appear in the trace.
- The answer should not be written back to cache because the response depends on booking, itinerary, disruption, and reaccommodation provenance.

Simple RAG contrast:
- Simple RAG can describe airline cancellations in general terms.
- It cannot know the signed-in traveller's booking locator, cancelled flight number, rebooked replacement flight, or next-step record.

## Path 2: Semantic Cache Showcase for Tier-Based Cancellation Help

Goal:
Show that entitlement-style guidance can be cached within a passenger cohort,
not across all passengers.

Opening prompt:
`What help do I usually get after a cancellation?`

Suggested passenger order:
1. `Mara Beck` (`Senator • EN`)
2. `Lena Hartmann` (`Senator • EN`)
3. `Jonas Klein` (`Frequent • EN`)

Expected tool sequence:
1. `get_current_user_profile`
2. `search_travelpolicydoc_by_text(value="status tier disruption help")`

Required supporting records:
- Shared policy docs covering disruption benefits by status tier
- Demo users with at least:
  - two `Senator • EN` passengers
  - one `Frequent • EN` passenger

Expected assistant behavior:
- State the signed-in traveller's tier in the answer.
- Keep the response at the shared program-guidance level.
- Do not turn the answer into a booking-specific promise.
- Do not fetch bookings, itinerary segments, disruption records, or support cases.

Expected semantic-cache behavior:
- First run as `Mara Beck`: `Semantic cache miss`, then `Semantic cache write`
- Second run as `Lena Hartmann` on a fresh thread with the exact same prompt:
  `Semantic cache hit`
- Third run as `Jonas Klein` on a fresh thread with the exact same prompt:
  should miss rather than reuse the `Senator • EN` answer

Simple RAG contrast:
- Simple RAG can summarize the same policy guidance.
- It cannot demonstrate cohort-aware reuse tied to the signed-in passenger context.

## Path 3: Semantic Cache Showcase for Shared Flight Status

Goal:
Show that a shared flight-number question can be cached for anyone.

Opening prompt:
`What is the status of ZX018 today?`

Suggested follow-up:
- `Which terminal is ZX018 departing from?`

Suggested passenger order:
1. Any passenger
2. Any different passenger on a fresh thread with the exact same prompt

Expected tool sequence:
1. `filter_operatingflight_by_flight_number`

Required supporting records:
- `OperatingFlight`: `OF_003` / `ZX018`

Expected assistant behavior:
- Treat the question as a shared flight lookup, not a traveller-booking lookup.
- Report status, route, scheduled timing, and terminal from the shared operating flight record.
- Mention that the gate is not yet assigned only if the record does not contain a gate.
- Avoid pulling booking or itinerary data unless the user pivots to their own trip.

Expected semantic-cache behavior:
- First run: `Semantic cache miss`, then `Semantic cache write`
- Second run from any other passenger on a fresh thread with the same prompt:
  `Semantic cache hit`

Simple RAG contrast:
- Simple RAG can describe how to check flight status in general.
- It cannot retrieve the live shared operating-flight record for `ZX018`.
