import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {CortexState} from './index.mjs';

test('rejects remote plaintext and missing credentials', () => {
  assert.throws(() => new CortexState({url: 'http://example.com', apiKey: 'key'}));
  assert.throws(() => new CortexState({}));
});

test('client sends scope and auth and propagates status', async () => {
  const server = createServer(async (req, res) => {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    const body = JSON.parse(raw);
    assert.equal(req.headers.authorization, 'Bearer test-key');
    assert.equal(body.scope.user, 'alice');
    res.setHeader('Content-Type', 'application/json');
    if (req.url.endsWith('/get')) {
      res.statusCode = 404;
      res.end(JSON.stringify({error: 'memory not found'}));
    } else res.end(JSON.stringify({result: {text: body.text}}));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const client = new CortexState({url: `http://127.0.0.1:${server.address().port}`, apiKey: 'test-key'});
    assert.deepEqual(await client.call('add', {scope: {user: 'alice'}, text: 'coffee'}), {text: 'coffee'});
    await assert.rejects(client.call('get', {scope: {user: 'alice'}, identifier: 'missing'}), {status: 404});
    await assert.rejects(client.call('../secrets', {scope: {user: 'alice'}}));
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});
