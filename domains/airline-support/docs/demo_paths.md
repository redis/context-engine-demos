# Demo Paths

These scripted paths are the source of truth for the `airline-support` domain.
Schema, prompt design, and generated data should all exist to support these
conversations cleanly.

> Tip: Run each opening question once in Context Surfaces mode and then repeat
> it in Simple RAG mode to show the difference between record-backed trip data
> and generic policy guidance.

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

Simple RAG contrast:
- Simple RAG can describe airline cancellations in general terms.
- It cannot know the signed-in traveller's booking locator, cancelled flight number, rebooked replacement flight, or next-step record.

## Path 2: Flight Status for the Next Confirmed Trip

Opening prompt:
`Flight status`

Follow-up:
- `Which terminal should I go to?`

Expected tool sequence:
1. `get_current_user_profile`
2. `filter_booking_by_customer_id`
3. `get_current_time`
4. `filter_itinerarysegment_by_booking_id`
5. `filter_operatingflight_by_operating_flight_id`

Required supporting records:
- `CustomerProfile`: `AIRCUST_001`
- `Booking`: `BOOK_002` / locator `ZX19MP`
- `ItinerarySegment`: `SEG_003` / `ZX018`
- `OperatingFlight`: `OF_003`

Expected assistant behavior:
- Treat a generic `Flight status` question as a request about the traveller's next relevant unaffected trip.
- Report the current status, route, scheduled timing, and terminal.
- Only mention a gate if the segment record actually includes one; otherwise say it has not been assigned yet.
- Avoid mixing this path with the disrupted booking unless the user explicitly pivots back.

Simple RAG contrast:
- Simple RAG can describe how to check a flight status.
- It cannot determine which flight is the traveller's next confirmed trip or cite the actual terminal and status from the booking records.

## Path 3: Traveller Profile Snapshot

Opening prompt:
`What does my travel profile say about my status?`

Follow-up:
- `What contact details do you have on file for me?`

Expected tool sequence:
1. `get_current_user_profile`
2. `filter_customerprofile_by_customer_id`

Required supporting records:
- `CustomerProfile`: `AIRCUST_001`

Expected assistant behavior:
- Return a read-only public-safe account summary.
- Cite the profile ID, masked loyalty number, loyalty tier, preferred language, email, and consent summary.
- Do not invent editable settings, hidden identifiers, or raw internal payload fields.

Simple RAG contrast:
- Simple RAG can explain what the traveller profile is.
- It cannot identify this traveller's actual profile, loyalty tier, or contact email on file.
