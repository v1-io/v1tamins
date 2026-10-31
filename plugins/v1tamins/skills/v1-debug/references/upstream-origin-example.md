# A reader guard leaves the writer broken

This synthetic example shows how evidence changes the scope of a correction.

An editor fails when it reads an imported record's `settings` field. The
contract requires a JSON object, but the importer serializes an already encoded
object. One decode returns a string. The reader then treats that string as an
object and fails.

## Probe the producer

The reader may decode incorrectly, or the importer may write the wrong shape.
The producer hypothesis predicts that a save-and-reload through the importer
returns a string after one decode. Search `settings` assignments and casts,
then inspect the importer's history. Keep the hypothesis open if stored-row
access is unavailable. Do not fetch the same restricted value through another
route or claim its shape is verified.

## Reproduce the actual path

Use the editor's load entry on unchanged code with synthetic incident-shaped
data. The object is `{"mode":"compact"}`. Its double-encoded JSON text is
`"{\"mode\":\"compact\"}"`. Add a variant with another valid mode.
A scalar placeholder such as `"marker"` cannot reproduce the double-encoding
mechanism. When row access is blocked, label the fixture's shape as a hypothesis.

## Cover the shared logic before correction

A symbol search finds the editor loader, the preview loader, and the settings
exporter. Both loaders apply the failing object lookup, so both are `in the
change`. The exporter preserves raw bytes without that lookup and is
`unaffected`. State that reason before editing.

## Classify the result

The origin fix changes the importer to encode once. A save-and-reload check
must return an object after one decode. Both loaders must accept that record
and the variant. Existing malformed rows still need repair.

If the current authorization excludes stored-data repair, a bounded read-side
decoder across both loaders can reduce impact. Its Fix class is `mitigated`.
Record the remaining malformed rows and assign their repair to the data owner.
If the writer is also unverified, record that gap and assign investigation to
the importer maintainer. Do not call the reader change a complete origin fix.
