# Verified stock assets for native-site handoffs

- Treat the project brief as binding: reject a recommender's pink/soft-UI/social-proof suggestions when the brand forbids them or the business is fictional.
- Verify each selected image's own source page, named photographer, image URL and link to a current license; a search snippet or an image CDN response alone does not establish rights.
- Save the actual extracted source and license text with the local asset manifest so a handoff survives a later page failure.
- Retrieve public images through their documented download links at a sensible width. Prefer ordinary curl with the CDN's usual resize query when urllib or optional format/fit parameters fail; do not bypass licensing, paywalls or authentication.
- Verify actual HTTP status, media type, decoding, dimensions, optimized byte size and SHA-256. Keep primary-source counts separate from derivative-file counts.
- Preserve full frames until a human or functioning vision tool can inspect crops; source captions are subject evidence, not a completed visual review.
- Never infer a treatment or its efficacy from a similar beauty photo: natural eyelashes are not proof of lamination, coating application does not identify gel chemistry, and stock staff/interiors are not the client's staff/interior.
- Use explicit stock/reference and fictional-demo labels at the photo gallery, price list and form; an inquiry success is not an appointment confirmation.
- Match native templates against the local catalogue's exact ID/code pair. Keep structured content separate from provider payload strings and never replace a requested native site with a giant HTML block.
- Generate optional SVGs through the required existing code engine, then parse XML, reject external/script content and rasterize to verify real outputs. Keep map placeholders abstract and visibly labelled as not directions.
- Record mechanical checks, font-width measurements, visual review, browser QA and delivery tests as separate evidence classes; a failure in one must never be relabelled as a pass in another.
