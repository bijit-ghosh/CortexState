//! Small, deterministic BM25 scoring primitive.
//! Corpus filtering and tokenization deliberately remain in CortexState's
//! portable Python layer so both implementations score identical inputs.

use std::collections::HashMap;

pub fn bm25_score(
    query_tokens: &[String],
    document: &[String],
    corpus_size: usize,
    document_frequencies: &HashMap<String, usize>,
    average_length: f64,
) -> f64 {
    let mut raw = 0.0_f64;
    let mut ordered_query = query_tokens.to_vec();
    ordered_query.sort();
    for word in &ordered_query {
        let frequency = document.iter().filter(|token| *token == word).count() as f64;
        if frequency == 0.0 {
            continue;
        }
        let df = *document_frequencies.get(word).unwrap_or(&0) as f64;
        let n = corpus_size as f64;
        let inverse = ((n - df + 0.5) / (df + 0.5)).ln_1p();
        let denominator = frequency + 1.2 * (0.25 + 0.75 * document.len() as f64 / average_length.max(1.0));
        raw += inverse * frequency * 2.2 / denominator;
    }
    raw
}

#[cfg(feature = "python")]
mod python {
    use super::bm25_score;
    use pyo3::prelude::*;
    use pyo3::types::PyDict;
    use std::collections::HashMap;

    #[pyfunction]
    fn bm25_batch(
        query_tokens: Vec<String>,
        documents: Vec<Vec<String>>,
        corpus_size: usize,
        frequencies: &Bound<'_, PyDict>,
        average_length: f64,
    ) -> PyResult<Vec<f64>> {
        let frequencies: HashMap<String, usize> = frequencies
            .iter()
            .map(|(key, value)| Ok((key.extract::<String>()?, value.extract::<usize>()?)))
            .collect::<PyResult<_>>()?;
        Ok(documents.iter().map(|document| {
            bm25_score(&query_tokens, document, corpus_size, &frequencies, average_length)
        }).collect())
    }

    #[pymodule]
    fn _rust_rank(module: &Bound<'_, PyModule>) -> PyResult<()> {
        module.add_function(wrap_pyfunction!(bm25_batch, module)?)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::bm25_score;
    use std::collections::HashMap;

    #[test]
    fn deterministic_score_ignores_absent_terms() {
        let query = vec!["rust".into(), "absent".into()];
        let doc = vec!["rust".into(), "core".into(), "rust".into()];
        let df = HashMap::from([("rust".into(), 1)]);
        let score = bm25_score(&query, &doc, 3, &df, 3.0);
        assert!(score.is_finite() && score > 0.0);
        assert_eq!(score, bm25_score(&query, &doc, 3, &df, 3.0));
    }

    #[test]
    fn empty_corpus_is_zero() {
        assert_eq!(bm25_score(&[], &[], 0, &HashMap::new(), 0.0), 0.0);
    }
}
