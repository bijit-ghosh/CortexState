export interface Scope { user: string; agent?: string; session?: string }
export interface MemoryRecord {
  id: string; text: string; metadata: Record<string, unknown>; revision: number;
  created_at: number; updated_at: number; expires_at: number | null;
}
export interface SearchResult extends MemoryRecord { score: number; signals: {lexical: number; semantic: number} }
export interface Scoped { scope: Scope }
export interface AddOptions extends Scoped { metadata?: Record<string, unknown>; ttl_seconds?: number; idempotency_key?: string }
export interface SearchOptions extends Scoped { limit?: number; metadata?: Record<string, unknown>; semantic_weight?: number; ranking?: 'overlap' | 'bm25' }
export interface ContextResult { data: string; characters: number; memory_ids: string[]; trust: string }
export interface Stats { total: number; live: number; expired: number; revision_events: number; last_updated_at: number | null; embedding_id: string }
export type LearningOutcome = 'success' | 'failure' | 'correction' | 'blocked' | 'unsafe';
export interface Experience { id: string; task: string; outcome: LearningOutcome; summary: string; source: Record<string, unknown>; measures: Record<string, unknown>; created_at: number; trust: 'untrusted_experience_data' }
export interface LearningEvaluation { id: string; suite: string; evaluator: string; heldout: boolean; total: number; baseline_passed: number; candidate_passed: number; safety_regressions: number; baseline_tokens: number; candidate_tokens: number; baseline_latency_ms: number; candidate_latency_ms: number; passed: boolean; created_at: number }
export interface LearningCandidate { id: string; category: string; content: string; status: string; evidence_ids: string[]; evaluation: LearningEvaluation | null; memory_id: string | null; approved_by: string | null; created_at: number; updated_at: number; trust: 'untrusted_candidate_data' }
export class CortexState {
  constructor(options: {url?: string; apiKey: string; timeoutMs?: number});
  call(operation: string, options: Scoped & Record<string, unknown>): Promise<unknown>;
  add(text: string, options: AddOptions): Promise<MemoryRecord>;
  search(query: string, options: SearchOptions): Promise<SearchResult[]>;
  get(identifier: string, options: Scoped): Promise<MemoryRecord>;
  update(identifier: string, text: string, options: Scoped & {expected_revision: number; metadata?: Record<string, unknown>}): Promise<MemoryRecord>;
  delete(identifier: string, options: Scoped & {expected_revision: number}): Promise<null>;
  list(options: Scoped & {limit?: number; offset?: number}): Promise<MemoryRecord[]>;
  history(identifier: string, options: Scoped): Promise<Array<{action: string; at: number; memory: MemoryRecord}>>;
  context(query: string, options: Scoped & {max_chars?: number; limit?: number; metadata?: Record<string, unknown>}): Promise<ContextResult>;
  stats(options: Scoped): Promise<Stats>;
  purgeExpired(options: Scoped): Promise<number>;
  propose(messages: Array<{role: 'user' | 'assistant'; content: string}>, options: Scoped): Promise<Array<{text: string; source_indices: number[]; status: string}>>;
  answer(question: string, options: Scoped): Promise<{answer: string; memory_ids: string[]; model: string; usage: {input_tokens: number | null; output_tokens: number | null}}>;
  recordExperience(experience: {task: string; outcome: LearningOutcome; summary: string; consent: true; source?: Record<string, unknown>; measures?: Record<string, number>; event_key?: string}, options: Scoped): Promise<Experience>;
  listExperiences(options: Scoped & {limit?: number; before?: number}): Promise<Experience[]>;
  listLearningCandidates(options: Scoped & {limit?: number; status?: 'candidate' | 'evaluated' | 'needs_revision' | 'promoting' | 'promoted' | 'rejected' | 'rolled_back'}): Promise<LearningCandidate[]>;
  proposeLesson(candidate: {evidence_ids: string[]; content: string; category?: 'lesson' | 'procedure' | 'preference' | 'constraint' | 'tool_strategy'}, options: Scoped): Promise<LearningCandidate>;
  evaluateLesson(id: string, scorecard: {suite: string; evaluator: string; heldout: true; total: number; baseline_passed: number; candidate_passed: number; safety_regressions: number; baseline_tokens: number; candidate_tokens: number; baseline_latency_ms: number; candidate_latency_ms: number}, options: Scoped): Promise<LearningCandidate>;
  promoteLesson(id: string, options: Scoped & {approvedBy: string}): Promise<LearningCandidate>;
  rejectLesson(id: string, options: Scoped & {reason: string}): Promise<LearningCandidate>;
  rollbackLesson(id: string, options: Scoped & {expectedRevision: number}): Promise<LearningCandidate>;
  deleteExperience(id: string, options: Scoped): Promise<{deleted: true; experience_id: string; derived_lessons_removed: number}>;
}
