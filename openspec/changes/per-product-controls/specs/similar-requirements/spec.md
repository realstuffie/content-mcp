## MODIFIED Requirements

### Requirement: Find similar requirements across frameworks
The system SHALL provide a `find_similar_requirements` MCP tool that finds requirements with similar text across all control frameworks using Jaccard text similarity. The tool SHALL accept `requirement_text` (str, required), `min_similarity` (float, default 0.2), `max_results` (int, default 20), `exclude_control_id` (str, optional), and `product` (str, optional). Results SHALL be sorted by similarity score descending.

When `product` is provided, the tool SHALL use product-aware discovery to build the index (global + product-specific directories with override semantics).

#### Scenario: Find similar requirements for a password policy text
- **WHEN** `find_similar_requirements` is called with `requirement_text: "The system must enforce password complexity requirements"`
- **THEN** the system returns a list of `SimilarRequirement` objects sorted by `similarity_score` descending, each containing the matching requirement's `control_id`, `requirement_id`, `title`, `description`, `rules`, `similarity_score`, and `matching_terms`

#### Scenario: Exclude a specific control framework
- **WHEN** `find_similar_requirements` is called with `exclude_control_id: "cis_rhel9"`
- **THEN** no results from the `cis_rhel9` framework are included

#### Scenario: Minimum similarity threshold filtering
- **WHEN** `find_similar_requirements` is called with `min_similarity: 0.5`
- **THEN** only requirements with Jaccard similarity >= 0.5 are returned

#### Scenario: Max results cap
- **WHEN** more matches exist than `max_results`
- **THEN** only the top `max_results` results (by similarity score) are returned

#### Scenario: No matches found
- **WHEN** `find_similar_requirements` is called with text that has no similarity to any requirement
- **THEN** the system returns an empty list

#### Scenario: Similarity search scoped to product
- **WHEN** `find_similar_requirements` is called with `product: "rhel9"`
- **THEN** the search SHALL include controls from global and `products/rhel9/controls/` (with override semantics), but not controls from other products

### Requirement: Tokenization for similarity
The system SHALL tokenize text by lowercasing, removing non-alphanumeric characters (keeping spaces), splitting on whitespace, removing stopwords (including compliance-domain stopwords: "ensure", "operating", "system", "information"), and filtering tokens shorter than 3 characters.

#### Scenario: Stopword removal
- **WHEN** the text "The system shall ensure information is protected" is tokenized
- **THEN** the tokens do not include "the", "shall", "ensure", "system", or "information"

#### Scenario: Short token filtering
- **WHEN** the text "OS is an IT system" is tokenized
- **THEN** the tokens do not include "os", "is", "an", or "it" (all 2 characters or fewer)

### Requirement: SimilarRequirement model
The system SHALL define a `SimilarRequirement` Pydantic model with fields: `control_id` (str), `requirement_id` (str), `title` (str), `description` (str), `rules` (list[str]), `similarity_score` (float, 0.0-1.0), `matching_terms` (list[str]).

#### Scenario: Matching terms populated
- **WHEN** a similar requirement is found
- **THEN** `matching_terms` contains the intersection of tokens between the query text and the requirement text
