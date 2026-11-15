# AI ad-creative systems: evidence, access, and money

Use when reviewing a video or vendor pitch that joins customer research, generated creatives, testing, and automatic ad-budget changes. Keep a research-only request separate from authorization to create paid assets, connect ad accounts, or publish campaigns.

## Identify what is actually being sold

Classify the deliverable as a downloadable tool, hosted studio, model API, agency implementation, or architecture description. A video of a workflow is not a public implementation of its connectors, approvals, or spend controls. Report which of those you inspected and which remain claims.

Treat "worth $25,000" as a publisher's valuation unless an actual offer establishes a price and scope. Treat revenue multipliers as unverified outcomes without comparable periods, spend, conversion definitions, attribution, margins, and a credible causal comparison. Constant ad spend does not imply constant total cost: account subscriptions, inference, creative production, and support remain separate.

## Separate signals from outcomes

Use reviews and public competitor ads to propose hypotheses, not to label guaranteed winners. An ad's continued presence does not expose its profitability; engagement, play time, clicks, purchases, and contribution margin are different outcomes.

Keep the evidence chain for an angle: source and quote → customer need → hypothesis → brief → creative version → campaign/ad ID → measured result. Validate product claims, prices, permissions, and brand fidelity before approval. Do not copy competitors' protected assets or invent endorsements.

Evaluate a small labeled sample before relying on bulk creative classification. A model's confidence belongs to the question it answered, not automatically to purchase probability, ROAS, or forecast revenue.

## Distinguish the model from the executor

Use a decision model for bounded judgments; use code for arithmetic, thresholds, counts, and dates, and a generator or template for prose. Jev is TypeSafe's underlying decision model; a Hermes routing plugin is only one integration of it, not an ad-management product.

Validate the selected adapter and version. A text-only host integration does not establish that the provider has no image API; experimental provider image support does not establish production readiness. Do not enable experimental/danger-zone features on client traffic just because a marketing demo uses them.

Keep classification and execution credentials separate. A label such as `scale` is a recommendation until deterministic policy, data freshness, authorization, and an account-specific writer accept it.

## Check the exact creative product and surface

Separate a browser game builder, network-formatted playable-ad exporter, and conventional image/video generator. The same vendor can put them behind different plans and interfaces.

Navigate, wait, extract, and save evidence in one browser call where possible. Assert the actual page URL and the required text before saving; a later call may begin on a blank or stale tab. An empty snapshot is not evidence that the feature is absent.

For Higgsfield specifically, check Playable Ads, Playable Games, and the API's Ads Studio independently. The reviewed public pages distinguish Enterprise Playable Ads from broadly available Games; a Games MCP path or image-generation endpoint does not prove a Playable Ads API entitlement. Recheck current documentation and the intended plan rather than carrying these as permanent limits.

A network export option is not a successful live upload or moderation approval. Verify the chosen network, campaign type, placement, SDK/click behavior, file-size limit, and destination URL with that network's current requirements. Do not equate Pangle with every TikTok placement, or a video cut with an interactive game. Verify VK/Yandex compatibility separately if not explicitly listed.

Name input-limit conflicts rather than silently selecting the larger number. Treat example UI costs and catalog floors as different from an account-specific price quote or final debit. Do not run a paid generation just to strengthen a desk review.

## Spend controls belong in code and the account

Start with recommendations-only and read-only metrics; add account writes only in an explicitly authorized pilot. New creatives, new offers, launch, and budget changes are separate approval scopes. A bounded pre-authorized policy may permit adjustments, but an approval to create a draft is not approval to spend.

Read the platform's actual budget semantics before promising a hard cap. An average daily budget is not necessarily the maximum bill for a day. Google documents that a budget-edit day's limit uses the highest average daily budget chosen that day for the campaign. Reallocating money between campaigns can therefore increase aggregate daily exposure while the sum of current budgets stays unchanged.

Account for timezone, currency, attribution delay, stale metrics, concurrent workers, pending writes, retry idempotency, and period boundaries. Refuse new writes on uncertainty; do not treat missing metrics as zero spend or automatically pause every campaign without a pre-agreed policy.

Reserve spend authority centrally rather than independently in each agent. Enforce campaign/account allowlists, permitted actions, maximum change size, cadence, and owner-approved overall exposure. Record before/after values, reason, source metrics, approval/policy version, and exact target. Read back the external target after a write. Do not promise cross-platform atomicity or instantaneous stop behavior.

Do not set universal "winner after 48 hours" rules. Choose sample and conversion maturity requirements from the business and experiment; low-volume data may be insufficient. Optimize against qualified leads, sales, or margin as appropriate, not creative taste or CTR alone.

## Report a bounded recommendation

Prefer the transferable loop—research, brief, controlled production, human approval, measurement, next hypothesis—over buying every named vendor. Compare against existing local capabilities without claiming they were tested in this review.

A useful first pilot can be ordinary image/video creatives plus a source-linked brief and outcome report, without playable-game costs or autonomous spend. Define acceptance criteria before requesting production access.

For provenance and the worked budget-limit example see `/root/kb/projects/restructure-ad-creative-system.md`. Its study scope is public documentation and DOM inspection, not proof that the agency's full system runs.
