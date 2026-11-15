# Validating what an LLM node actually returns

Applies when a workflow's chain is `AI Agent` (or any LLM node) → a send/publish
node that forwards the model's text to a live channel. The retrieval may be
perfect and the user still receives garbage, because the LLM node's output is
provider-controlled. This is a different class of bug from a broken prompt or a
bad retriever, and it is invisible to every check that stops at the context the
retriever built.

## A retired model: active workflow, no reply

When the user reports silence, read the failed execution before testing content guards. An OpenRouter `404` whose description says the configured model is "no longer available" / "no provider serves this model anymore" is provider retirement, not a broken Telegram webhook or a bad knowledge-base query. Confirm the exact model id in `activeVersion.nodes`, compare it with the historical execution's model parameter, and check the public `GET https://openrouter.ai/api/v1/models` catalog. Catalog membership is only an availability hint, not proof of account access or a successful generation.

Trace all boundaries: Telegram input, knowledge-base fetch/search, model call, reply guard, send. A guard after `AI Agent` cannot catch a thrown model exception when the agent uses `stopWorkflow`; it never runs. Treat replacing the retired id and adding an explicit error/fallback branch as separate changes requiring scope approval. Do not retry a retired id, restart shared n8n, rotate working credentials, or replay failed user messages during diagnosis.

For a replacement, inspect output modalities and use a named text-generation model: zero prompt/completion pricing alone also matches audio and moderation models, and a free-router alias can reintroduce the metadata-output defect below. Verify the chosen model with the actual prompt and a delivered response after approval; listing it in the catalog does not complete recovery.

For an AI Agent v3 with an existing output guard, a separate error branch is not required: set the agent's `onError` to `continueRegularOutput` and detect the resulting `{error: message}` before validating `output`. The installed `ToolsAgent/V3/helpers/executeBatch.js` emits that envelope when `ctx.continueOnFail()` is true; `BaseExecuteContext.continueOnFail()` maps both continue modes to true. Return a fixed service-unavailable reply without exposing the exception, and preserve the existing send node's chat reference and graph. Test the guard on a captured exception, structured and empty errors, mixed `error` + stale `output`, normal text and existing junk fixtures. Offline tests prove handling logic, not a live provider response or delivered Telegram message.

When comparing an isolated execution against the published workflow, account for SDK-inserted defaults in `execution.workflowData`: absent UI notices may appear as empty strings, absent `hasOutputParser`/`needsFallback` as false, and absent Code mode/language as `runOnceForAllItems`/`javaScript`. Compare the actual prompt text, system message/options, guard source, resolved model and credential reference; normalize only documented defaults, never arbitrary differences. A whole-parameters equality failure can otherwise be a harness false alarm rather than a changed test prompt.

## The signature: a `success` run that delivers junk

The execution reports `status: success`, every node has
`executionStatus: success`, the send node returns `ok: true` with a real
`message_id`, and token counters show the model generated output. The user
received provider metadata instead of an answer.

```
ex 2635  success  9 nodes  ok:true  msg_id 346
        agent output: 'User Safety: safe\nResponse Safety: safe'
```

Every health signal says green. `status: success` means the chain ran, not that
the content was an answer. **Assert on the text that landed, never on the
status.**

## Diagnose: read the model's output field, then blame the least likely node first

Read `runData["AI Agent"]`'s output and dump **all** its keys. If the value the
send node forwards is already the junk string, the defect is in the LLM node or
its model — the retriever ran earlier and cannot be responsible, because its
output feeds the agent as input rather than replacing the agent's output.

Check `metadata.tracing` for `llm.tokens.in` / `llm.tokens.out`. Non-zero
output tokens with a junk string prove the provider returned content and the
client accepted it, which rules out "the model was never called". A `0` in
`llm.tokens.out` would instead mean the response never arrived.

Then check the model node's `parameters.model`:

- **`openrouter/free` (or any free-router alias) is a roulette wheel.** It
  resolves per request to different free models from different providers, each
  with its own response envelope conventions. A workflow that returned correct
  text five runs in a row and junk on the sixth, with no edit in between, is
  this — not a regression, not the prompt, not a quota problem.
- **A named model pins the format.** Replacing the router alias with a concrete
  `provider/model` id removes the cross-provider format variation. Confirm the id
  exists on the account before shipping; a free route can still rate-limit, but
  it stops returning a different envelope shape each call.

To attribute a break to the provider rather than to your edit, sweep retained
executions and compare the output string against the window when the change
landed:

```
sweep /executions?workflowId=<id> for the junk substring
ex 2156  ok   'Слушай сюда. Номинал: 1,0–1,1 мм…'
ex 2600  ok   'Сбросить ошибки ABS без сканера…'
ex 2635  JUNK 'User Safety: safe\nResponse Safety: safe'
```

A break that starts mid-window with no code change in that window is external.
This matters for what you tell the user: "your edit broke it" and "the provider
changed" lead to opposite decisions, and shipping a revert for an external fault
wastes the session.

## Ship both halves: pin the cause, and guard the symptom

Pinning a model removes the trigger but not the class — the next provider quirk,
quota response, or content-filter interjection still reaches the channel. Add a
guard Code node between the agent and the send node.

```
AI Agent -> Проверка ответа -> Send a text message
```

The guard re-emits `{ output, garbageDetected, rawOutput }`, so the send node's
existing `{{ $json.output }}` expression keeps working unchanged. Test rules:

- **known provider junk strings, checked first, by substring not equality.** The
  provider may append its own text to the marker, so `lower.indexOf(g) !== -1`
  over a list of markers beats `list.includes(lower)`. Testing by full equality
  passes a harness whose every case is the bare marker and then misses the
  `User Safety: safe — всё понятно` variant in production.
- **no Cyrillic in a corpus that answers in Cyrillic** — a proxy for "not prose".
- **a minimum length floor** — catches truncations and one-word stubs.

Order matters: evaluate the junk markers before the Cyrillic test, or a marker
with appended Russian text reads as valid prose and ships.

Test the guard against outputs captured from real executions, both good and junk,
and assert the count. A guard exercised only on the string that motivated it is a
guard with untested branches.

## Reporting shape for this failure

State the split plainly, because the user is looking at a bot that "works":

- the retrieval result (which was correct, and prove it from the retriever
  node's own context in the execution);
- the model result (which was junk, with the literal string);
- the fix, in two parts, with what each part does and does not cover;
- what is still unverified — a guard tested offline has not been seen on a live
  run, and a newly pinned model has not been exercised on Russian technical text
  with this prompt. Say so, and name the message that would settle it.

Do not fold the model pin into a retriever fix as one change. They are different
failure domains; bundling them means a regression in either is hard to attribute
and the user approved one thing while receiving another.