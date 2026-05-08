# Northbridge Banking Demo Paths

## Path 1: Shared product-guidance cache

Goal: show an identity-free semantic-cache hit for public product guidance.

1. Start a fresh thread as any customer.
2. Prompt: `How do card controls work in the Northbridge app?`
3. Expected behavior:
   - semantic cache miss on the first run
   - `search_supportguidancedoc_by_text(value="card controls")`
   - semantic cache write after the answer completes
4. Start a second fresh thread as a different customer.
5. Repeat the same prompt.
6. Expected behavior:
   - semantic cache hit

Optional follow-up:
- `Can I freeze and unfreeze my card there?`

## Path 2: Cohort-scoped support guidance

Goal: show a cache write and hit that stay within the signed-in support segment.

1. Start a fresh thread as `Maya Chen` (`Plus`).
2. Prompt: `What help do I usually get if something looks wrong with my card?`
3. Expected behavior:
   - semantic cache miss
   - `get_current_user_profile`
   - `search_supportguidancedoc_by_text(value="card issue support routing")`
   - semantic cache write scoped to `plus_en`
4. Start a fresh thread as `Jordan Lee` (`Plus`).
5. Repeat the same prompt.
6. Expected behavior:
   - semantic cache hit
7. Start a fresh thread as `Casey Alvarez` (`Standard`).
8. Repeat the same prompt.
9. Expected behavior:
   - semantic cache miss because the cohort is different

## Path 3: Flagship card-decline recovery

Goal: show full multi-entity reasoning over live customer records.

Use `Maya Chen`.

1. Prompt: `My card was declined. What happened?`
2. Expected behavior:
   - `get_current_user_profile`
   - `filter_depositaccount_by_customer_id`
   - `filter_debitcard_by_account_id`
   - `filter_cardauthorisation_by_card_id`
   - `filter_cardriskevent_by_linked_authorisation_id`
   - `filter_cardsupportintervention_by_risk_event_id`
3. Expected answer:
   - the declined merchant was `Harbor Tech Online`
   - Northbridge Bank temporarily blocked card ending `4812`

Continue on the same thread:

4. Prompt: `That temporary block does not work for me. What else can I do?`
5. Expected behavior:
   - `filter_cardrecoveryoption_by_account_id`

Then:

6. Prompt: `Unfreeze it after verification.`
7. Expected behavior:
   - `get_current_user_profile`
   - `filter_depositaccount_by_customer_id`
   - `submit_card_recovery_selection`

Accepted recovery selections in this demo:
- Plain-language labels such as `Unfreeze it after verification.`
- Stable option codes such as `UNFREEZE_AFTER_VERIFICATION`

Optional final follow-up:
- `Show me my current card status.`
