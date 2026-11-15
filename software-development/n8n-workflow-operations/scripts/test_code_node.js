#!/usr/bin/env node
// Offline harness for an n8n Code node's jsCode.
//
// Usage:
//   node test_code_node.js <file-with-jsCode> <json-file-input> [json-file-names]
//
//   input  : JSON array of item objects (what the node receives on $input.all())
//   names  : JSON object mapping node name -> item json, for $('Node name')
//
// Prints the node's return value, or "THROWN: <message>" so a failing throw is
// as visible here as it would be in an execution log.

const fs = require('fs');

const [, , codePath, inputPath, namesPath] = process.argv;
if (!codePath || !inputPath) {
  console.error('usage: test_code_node.js <jsCode-file> <input-json> [names-json]');
  process.exit(2);
}

const INPUT = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const NAMEJSON = namesPath ? JSON.parse(fs.readFileSync(namesPath, 'utf8')) : {};
const code = fs.readFileSync(codePath, 'utf8');

const $json = INPUT[0];
const $input = { all: () => INPUT.map((json) => ({ json })) };
const $ = (name) => ({ item: { json: NAMEJSON[name] || {} } });
const $execution = { id: 'offline-harness' };
const $workflow = { id: 'offline-harness', name: 'offline-harness', active: false };
const $getWorkflowStaticData = () => ({});

let runner;
try {
  runner = new Function(
    'INPUT', 'NAMEJSON', '$json', '$input', '$', '$execution', '$workflow',
    '$getWorkflowStaticData',
    `return (async () => { ${code} })();`
  );
} catch (e) {
  console.log('SYNTAX ERROR: ' + e.message);
  process.exit(1);
}

Promise.resolve(
  runner(INPUT, NAMEJSON, $json, $input, $, $execution, $workflow, $getWorkflowStaticData)
)
  .then((out) => {
    const rows = Array.isArray(out) ? out : [out];
    console.log(JSON.stringify(out, null, 1));
    console.log(`\n// returned ${rows.length} item(s)`);
  })
  .catch((e) => {
    console.log('THROWN: ' + e.message);
    process.exit(1);
  });