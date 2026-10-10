# Field contract between adjacent nodes

A chain breaks silently when a downstream node references a key the upstream
node does not emit. n8n does not warn: the expression resolves to its own
literal text, the request ships with `{{ ... }}` inside the payload, and the
failure surfaces as a remote API validation error that quotes the template.

## Rule out the syntax cause before the rename cause

An API error that echoes your template text (`Invalid message_id: {{ $json.x }}`)
has TWO possible causes and they produce byte-identical errors:

1. **The expression never ran.** Any HTTP-node string parameter that must
   interpolate has to begin with `=`; without it n8n ships the literal. This is
   the more common cause and it looks exactly like case 2.
2. **The expression ran and named a field nobody emits.**

Triage in this order, because case 1 sends you auditing every emission map for
a mismatch that does not exist:

```python
# case 1: compare this node's parameter prefix with a sibling HTTP node that works
print(repr(Pin_node["parameters"]["jsonBody"]))
print(repr(Edit_node["parameters"]["jsonBody"]))   # working: starts with '='
```

`JSON.stringify($json.x)` already returns a quoted string, so the template must
not add its own quotes: `'={"message_id": {{ JSON.stringify($json.x) }}}'`, not
`'=...{{ JSON.stringify($json.x) }}...'`. Only after confirming the `=` prefix
is present do you go looking for renamed fields.

## Why it is silent

- Code nodes that `return [{ json: {...} }]` control the whole downstream
  vocabulary. Rename a key and every reference to the old name becomes a
  literal.
- n8n resolves expressions per node field, not per data path, so a bad key is
  indistinguishable from an intentionally literal string unless you read the
  emitted item.
- Typical upstream outputs to treat as the contract: a Code node that
  normalizes to `{ group_message_id }`, a Supabase `update` returning full rows
  (`id`, `slot_index`, `status`, `start_time`, ...), a MAX message node that
  returns the whole message envelope (`body.mid`, not `message_id`).

## Procedure

1. Build the emission map from the workflow JSON, not from memory:

   ```python
   for n in wf["nodes"]:
       if n["type"] == "n8n-nodes-base.code":
           print("==", n["name"]); print(n["parameters"]["jsCode"])
   ```

   For a Code node, the keys it emits are the literal keys of the object it
   returns; for HTTP/Supabase nodes, the reference shape (`body.mid`,
   `jsonBody`) is the contract.

2. List every expression in every node and classify it as `data` or `literal`:

   ```python
   import re
   for n in wf["nodes"]:
       blob = json.dumps(n["parameters"], ensure_ascii=False)
       for ref in re.findall(r"\{\{\s*\$[^}]+\}\}", blob):
           print(n["name"], "->", ref)
   ```

   A reference into a field that is not a data expression is a red flag.

3. Cross-check each `data` reference against the emission map. Field names in
   a URL, `jsonBody`, or text template count the same as ones in an `if`.

4. Settle it on a real execution rather than by reasoning: dump the failing
   node's input items and its parameters from one execution body. Dumping
   `sorted(json.keys())` matters — reading a hand-picked subset (`["date"]`)
   reports `date: null` for a node that emits the value under a different,
   correct name (`slot_date`), which fabricates a bug and sends you arguing
   with the user about a defect that was never there. Comparing inputs catches
   a genuine mismatch in one look — upstream emitted `group_message_id`, the
   body asked for `message_id`.

## The input side of the contract: what the PREVIOUS node emits

The key-name check above covers what an expression names. Equally silent is a
Code node whose INPUT is not the record it assumes, because a chat/message send
node returns the whole envelope it posted (`recipient`, `timestamp`, `body`,
`sender`) and not the business fields it was handed.

Symptom: the node returns `[]` instead of throwing, so the branch dies on an
empty output and everything after it never runs — no error naming the cause.
This is the shape to check whenever a node does `$input.all()` and finds
nothing:

```
KeyError-style field names aside, print the node's actual input:
MAX Bot Trigger Polling / Code: результат лока  ->  [1]
MAX: подтверждение клиенту                       ->  [1]   # only body/sender/timestamp
```

Fix by sourcing from the node that OWNS the data rather than from whatever
happens to be wired upstream: reference `$('<Node that produced the record>')`
directly instead of `$input`. Rule of thumb for every node in a fan-out branch:
a node connected after a SEND node gets the sent message, not the record that
was sent — if it needs the record, reach back past the sender.

## Side-effect nodes decide the group's state, not just its text

When a branch re-publishes a summary, check WHICH node writes it. A `SendToChat`
followed by `Pin` on the new mid creates a SECOND post while the original stays
pinned and stale; an `Edit Message` on the stored mid updates in place. An
`Edit Message` node sitting `disabled: true` next to an enabled send+pin pair is
this bug already committed — surface it as a finding with the user's choice
between the two behaviours, not as a cleanup.

## Cheap regression check

After renaming anything in a Code node, grep the whole workflow for the old
name before activating:

```
search for the previous key in every node's parameters
```

An old name surviving in one HTTP body is the whole bug; a rename that touched
four nodes and missed the fifth looks identical in the graph and differs only
in the remote response.