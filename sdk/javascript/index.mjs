/** CortexState client. Server-side use only; API keys authorize a whole tenant. */
const learningPaths = {
  'learning-record': 'record', 'learning-list': 'list', 'learning-candidates': 'candidates',
  'learning-propose': 'propose', 'learning-evaluate': 'evaluate',
  'learning-promote': 'promote', 'learning-reject': 'reject', 'learning-rollback': 'rollback',
  'learning-delete-experience': 'delete-experience',
};

export class CortexState {
  constructor({url = 'http://127.0.0.1:8787', apiKey, timeoutMs = 15000}) {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) {
      throw new Error('Provide an HTTP(S) service URL without credentials, query, or fragment');
    }
    if (parsed.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(parsed.hostname)) {
      throw new Error('Remote connections require HTTPS');
    }
    if (typeof apiKey !== 'string' || !apiKey) throw new Error('apiKey is required');
    this.url = url.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.timeoutMs = timeoutMs;
  }
  async call(operation, {scope, ...payload}) {
    if (!['add', 'get', 'list', 'search', 'update', 'delete', 'history', 'context', 'stats', 'propose', 'answer', 'purge-expired', ...Object.keys(learningPaths)].includes(operation)) {
      throw new Error('Unknown operation');
    }
    const path = learningPaths[operation]
      ? `/v1/learning/${learningPaths[operation]}`
      : `/v1/memories/${operation}`;
    const response = await fetch(`${this.url}${path}`, {
      method: 'POST', headers: {'Authorization': `Bearer ${this.apiKey}`, 'Content-Type': 'application/json'},
      body: JSON.stringify({...payload, scope}), signal: AbortSignal.timeout(this.timeoutMs),
      redirect: 'error',
    });
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.error || 'CortexState request failed');
      error.status = response.status;
      throw error;
    }
    return data.result;
  }
  add(text, options) { return this.call('add', {...options, text}); }
  search(query, options) { return this.call('search', {...options, query}); }
  get(identifier, options) { return this.call('get', {...options, identifier}); }
  update(identifier, text, options) { return this.call('update', {...options, identifier, text}); }
  delete(identifier, options) { return this.call('delete', {...options, identifier}); }
  list(options) { return this.call('list', options); }
  history(identifier, options) { return this.call('history', {...options, identifier}); }
  context(query, options) { return this.call('context', {...options, query}); }
  stats(options) { return this.call('stats', options); }
  purgeExpired(options) { return this.call('purge-expired', options); }
  propose(messages, options) { return this.call('propose', {...options, messages}); }
  answer(question, options) { return this.call('answer', {...options, question}); }
  recordExperience(experience, {scope}) { return this.call('learning-record', {...experience, scope}); }
  listExperiences({scope, ...options}) { return this.call('learning-list', {...options, scope}); }
  listLearningCandidates({scope, ...options}) { return this.call('learning-candidates', {...options, scope}); }
  proposeLesson(candidate, {scope}) { return this.call('learning-propose', {...candidate, scope}); }
  evaluateLesson(id, scorecard, {scope}) { return this.call('learning-evaluate', {...scorecard, identifier: id, scope}); }
  promoteLesson(id, {scope, approvedBy}) { return this.call('learning-promote', {identifier: id, approved_by: approvedBy, scope}); }
  rejectLesson(id, {scope, reason}) { return this.call('learning-reject', {identifier: id, reason, scope}); }
  rollbackLesson(id, {scope, expectedRevision}) { return this.call('learning-rollback', {identifier: id, expected_revision: expectedRevision, scope}); }
  deleteExperience(id, {scope}) { return this.call('learning-delete-experience', {identifier: id, scope}); }
}
