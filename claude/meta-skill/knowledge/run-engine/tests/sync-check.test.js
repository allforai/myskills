const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const dir = path.join(__dirname, '..')
const START = '// <<<ENGINE-CORE-START>>>'
const END = '// <<<ENGINE-CORE-END>>>'

function coreRegion(file) {
  const src = fs.readFileSync(path.join(dir, file), 'utf8')
  const a = src.indexOf(START)
  const b = src.indexOf(END)
  assert.ok(a !== -1 && b !== -1 && b > a, `markers missing/ordered wrong in ${file}`)
  return src.slice(a, b + END.length).trim()
}

test('workflow shell inlines engine-core verbatim (no drift)', () => {
  assert.equal(coreRegion('run-engine.workflow.js'), coreRegion('engine-core.js'))
})

test('workflow shell has the meta block and invokes runEngine', () => {
  const src = fs.readFileSync(path.join(dir, 'run-engine.workflow.js'), 'utf8')
  assert.match(src, /export const meta = \{/)
  assert.match(src, /runEngine\(\s*\{\s*agent/)
})

test('workflow shell does NOT require/import engine-core (sandbox-safe)', () => {
  const src = fs.readFileSync(path.join(dir, 'run-engine.workflow.js'), 'utf8')
  assert.doesNotMatch(src, /require\(|import .* from/)
})
