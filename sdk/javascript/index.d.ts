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
}
