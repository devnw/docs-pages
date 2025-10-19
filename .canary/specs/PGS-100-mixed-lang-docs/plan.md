# Implementation Plan: PGS-100 Mixed-Language Documentation Processing

**Requirement:** PGS-100
**Specification:** .canary/specs/PGS-100-mixed-lang-docs/spec.md
**Status:** STUB → IMPL
**Created:** 2025-10-19
**Updated:** 2025-10-19

## Tech Stack Decision

### Primary Technologies
- **Language:** Python 3.11+ (GitHub Actions standard)
- **Go Processing:** godocdown (existing dependency) + go/ast package
- **Zig Processing:** Native `zig build-* -femit-docs` commands (Zig 0.11+)
- **Rendering:** MkDocs Material 9.4+ (existing dependency)
- **Testing:** pytest 7.4+ with real file fixtures
- **Performance:** cProfile for benchmarking, no external dependencies

### Rationale
- **Python**: GitHub Actions native, extensive standard library for file processing
- **godocdown**: Existing Go documentation tool, maintains consistency with current workflow
- **Zig native docs**: Use `zig build-* -femit-docs` for official documentation generation
- **MkDocs Material**: Existing theme, supports syntax highlighting for both languages
- **pytest**: Standard Python testing, supports real file I/O testing per Article VI
- **No additional dependencies**: Follows Article V (Simplicity) - use native tools where possible

## Architecture Overview

### Component Diagram
```
Repository Scan → Language Detection → File Categorization
                                              ↓
Go Files → Go Processor → Go Documentation → Unified Renderer → MkDocs Site
                                              ↑
Zig Files → Zig Build Commands → Zig HTML Docs → HTML Parser ↗
                                              ↑
Cross-Reference Resolver ← Documentation Metadata
```

### Key Components

**Component 1: Language Detection Engine**
- **Responsibility:** Scan repository, identify .go/.zig files, categorize by language
- **Interfaces:** `detect_languages(repo_path: str) -> Dict[str, List[str]]`
- **Dependencies:** None (uses os.walk, pathlib)

**Component 2: Go Documentation Processor**
- **Responsibility:** Parse Go files, extract documentation, generate markdown
- **Interfaces:** `process_go_files(files: List[str]) -> List[DocPage]`
- **Dependencies:** LanguageDetection, godocdown subprocess

**Component 3: Zig Documentation Processor**
- **Responsibility:** Execute zig build commands with -femit-docs, parse generated HTML
- **Interfaces:** `process_zig_files(files: List[str]) -> List[DocPage]`
- **Dependencies:** LanguageDetection, Zig compiler, HTML parser

**Component 4: Unified Documentation Renderer**
- **Responsibility:** Combine Go/Zig docs, create navigation, generate MkDocs structure
- **Interfaces:** `render_unified_docs(go_docs: List[DocPage], zig_docs: List[DocPage]) -> MkDocsSite`
- **Dependencies:** GoDocProcessor, ZigDocProcessor, CrossRefResolver

**Component 5: Cross-Reference Resolver**
- **Responsibility:** Detect and link cross-language references
- **Interfaces:** `resolve_cross_references(docs: List[DocPage]) -> List[DocPage]`
- **Dependencies:** DocMetadata

## Work DAG & Concurrency Groups

### CG-1: Foundation (Parallel)
- **Task 1.1:** Create DocMetadata schema and models
- **Task 1.2:** Set up test fixtures with real Go/Zig files
- **Task 1.3:** Create language detection engine
- **Join Point:** All foundation components complete before processors

### CG-2: Language Processors (Parallel)
- **Task 2.1:** Implement Go documentation processor
- **Task 2.2:** Implement Zig documentation processor
- **Task 2.3:** Create cross-reference resolver
- **Join Point:** Both processors complete before unified renderer

### CG-3: Integration & Testing (Sequential)
- **Task 3.1:** Implement unified renderer
- **Task 3.2:** Create integration tests
- **Task 3.3:** Performance testing and optimization
- **Task 3.4:** Documentation and usage examples

## CANARY Token Placement

### Token Evolution: STUB → IMPL → TESTED → BENCHED

**Main Requirement Token:**
```python
# File: src/main.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="MixedLangDocs"; ASPECT=Docs; STATUS=IMPL; UPDATED=2025-10-19
```

**Sub-Feature Tokens:**
```python
# File: src/detection/language_detector.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="LanguageDetection"; ASPECT=Engine; STATUS=IMPL; TEST=TestLanguageDetection; UPDATED=2025-10-19

# File: src/processors/go_processor.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="GoDocProcessor"; ASPECT=Engine; STATUS=IMPL; TEST=TestGoDocProcessor; UPDATED=2025-10-19

# File: src/processors/zig_processor.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="ZigDocProcessor"; ASPECT=Engine; STATUS=IMPL; TEST=TestZigDocProcessor; UPDATED=2025-10-19

# File: src/renderers/unified_renderer.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="UnifiedRenderer"; ASPECT=Engine; STATUS=IMPL; TEST=TestUnifiedRenderer; UPDATED=2025-10-19

# File: src/resolvers/cross_ref_resolver.py (line 1)
# CANARY: REQ=PGS-100; FEATURE="CrossRefResolver"; ASPECT=Engine; STATUS=IMPL; TEST=TestCrossRefResolver; UPDATED=2025-10-19
```

## Implementation Phases (Test-First)

### Phase 0: Pre-Implementation Gates

**Simplicity Gate (Constitution Article V):**
- [x] Using Python standard library for file operations
- [x] No additional dependencies beyond existing godocdown
- [x] Custom Zig parser using standard Python tools only

**Test-First Gate (Constitution Article IV):**
- [x] All test functions defined before implementation
- [x] Test data fixtures prepared with real Go/Zig files
- [x] Expected failure messages documented

### Phase 1: Tests (Red Phase)

**Unit Tests (Expected to FAIL initially):**
```python
# tests/unit/test_language_detection.py
def test_detect_languages_mixed_repo():
    """Should identify both .go and .zig files correctly"""
    # Expected: FileNotFoundError (no implementation yet)

def test_detect_languages_go_only():
    """Should handle Go-only repositories"""
    # Expected: FileNotFoundError

def test_detect_languages_zig_only():
    """Should handle Zig-only repositories"""
    # Expected: FileNotFoundError

# tests/unit/test_go_processor.py
def test_process_go_files_with_docs():
    """Should extract Go documentation comments"""
    # Expected: ImportError (no go_processor module)

def test_process_go_files_malformed():
    """Should handle malformed Go documentation gracefully"""
    # Expected: ImportError

# tests/unit/test_zig_processor.py
def test_process_zig_files_with_docs():
    """Should extract Zig documentation comments (/// format)"""
    # Expected: ImportError (no zig_processor module)

def test_process_zig_files_comptime():
    """Should handle Zig comptime functions"""
    # Expected: ImportError

def test_process_zig_files_with_build_commands():
    """Should execute zig build-* -femit-docs commands successfully"""
    # Expected: ImportError

def test_process_zig_files_compilation_failure():
    """Should handle Zig compilation failures gracefully"""
    # Expected: ImportError

# tests/unit/test_unified_renderer.py
def test_render_mixed_language_docs():
    """Should create unified navigation for Go and Zig docs"""
    # Expected: ImportError (no unified_renderer module)

def test_render_single_language_docs():
    """Should handle single-language repositories"""
    # Expected: ImportError
```

**Integration Tests (Expected to FAIL initially):**
```python
# tests/integration/test_end_to_end.py
def test_full_documentation_generation():
    """Should generate complete MkDocs site from mixed repo"""
    # Expected: FileNotFoundError (no main implementation)

def test_performance_large_repository():
    """Should complete in < 2 minutes for 1000+ files"""
    # Expected: FileNotFoundError
```

### Phase 2: Implementation (Green Phase)

**Incremental Implementation Order:**
1. **Language Detection Engine** (enables all other components)
2. **DocMetadata Models** (foundation for all processors)
3. **Go Documentation Processor** (leverages existing godocdown)
4. **Zig Documentation Processor** (uses native zig build-* -femit-docs commands)
5. **Cross-Reference Resolver** (depends on both processors)
6. **Unified Renderer** (combines all components)

**Minimal Implementation Strategy:**
- Start with simplest possible implementation that passes tests
- Add complexity only when tests require it
- Use real file I/O throughout (no mocks per Article VI)
- Leverage native Zig documentation generation instead of custom parsing

### Zig Documentation Implementation Details

**Native Zig Commands:**
```bash
# For executable projects
zig build-exe -femit-docs src/main.zig

# For library projects  
zig build-lib -femit-docs src/lib.zig

# For object files
zig build-obj -femit-docs src/module.zig

# For test files
zig test -femit-docs src/tests.zig
```

**Implementation Approach:**
1. **Detection Phase:** Identify Zig files and determine project type (exe/lib/obj/test)
2. **Compilation Phase:** Execute appropriate `zig build-* -femit-docs` command
3. **Parsing Phase:** Parse generated HTML from `./docs/` folder
4. **Integration Phase:** Convert Zig HTML docs to MkDocs-compatible format

**Error Handling:**
- If Zig compilation fails, fall back to file-level parsing
- Log compilation errors for debugging
- Continue processing other files if individual files fail

### Phase 3: Benchmarks (Performance-Critical)

**Performance Targets:**
- Repository scan: < 5 seconds for 1000 files
- Go processing: < 30 seconds for 500 Go files
- Zig processing: < 60 seconds for 500 Zig files (includes compilation time)
- Total generation: < 2.5 minutes for mixed repo with 1000 files

**Benchmark Tests:**
```python
# tests/benchmarks/test_performance.py
def benchmark_language_detection():
    """Measure file scanning performance"""
    # Target: < 5 seconds for 1000 files

def benchmark_go_processing():
    """Measure Go documentation generation"""
    # Target: < 30 seconds for 500 files

def benchmark_zig_processing():
    """Measure Zig documentation generation (including compilation)"""
    # Target: < 60 seconds for 500 files

def benchmark_zig_compilation_only():
    """Measure Zig compilation time separately from HTML parsing"""
    # Target: < 45 seconds for 500 files
```

### Phase 4: Hardening

**Security Considerations:**
- File path validation to prevent directory traversal
- Input sanitization for documentation content
- Safe subprocess execution for godocdown calls

**Resiliency Features:**
- Graceful handling of malformed source files
- Partial success when some files fail to process
- Comprehensive error logging and reporting

**Observability:**
- Progress logging for long-running operations
- Performance metrics collection
- Error rate monitoring

## Testing Strategy

### Coverage Targets
- **Unit Tests:** 90% line coverage for all processors
- **Integration Tests:** 100% of user scenarios covered
- **Performance Tests:** All success criteria measured

### Test Data Fixtures
- **Real Go files:** 10 files with various documentation patterns
- **Real Zig files:** 10 files with comptime functions and error handling
- **Mixed repository:** 20 files (10 Go, 10 Zig) with cross-references
- **Edge cases:** Malformed comments, empty files, binary files

### CI Integration
- Run tests on Python 3.11, 3.12
- Performance regression detection
- Memory usage monitoring
- Real file I/O testing (no mocks)

## Risk & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Zig compilation failures | Medium | Medium | Graceful fallback to file-level parsing for broken Zig files |
| Performance degradation | Medium | Medium | Implement incremental processing, add caching layer if needed |
| Cross-reference false positives | Medium | High | Conservative detection with manual override configuration |

### Rollback Plan
- Feature flag to disable Zig processing
- Fallback to Go-only documentation generation
- Manual configuration override for problematic files
- Fallback to file-level parsing if Zig compilation fails

## Constitutional Gates

### Article I Gate: CANARY Token Primacy
- **Status:** PASS
- **Evidence:** All components have precise CANARY tokens with file paths
- **Verification:** Tokens specify exact implementation locations

### Article IV Gate: Test-First Development
- **Status:** PASS
- **Evidence:** All test functions defined before implementation
- **Verification:** Tests written with expected failure messages

### Article V Gate: Simplicity and Anti-Abstraction
- **Status:** PASS
- **Evidence:** No additional dependencies, uses native Zig tools
- **Verification:** Leverages existing Zig compiler instead of custom parsing

### Article VI Gate: Integration-First Testing
- **Status:** PASS
- **Evidence:** Real file I/O testing, no mocks
- **Verification:** Test fixtures use actual Go/Zig source files

### Security Gate
- **Status:** PASS
- **Threats:** Directory traversal, subprocess injection, Zig compilation exploits
- **Mitigations:** Path validation, safe subprocess execution, sandboxed Zig compilation

### Performance Gate
- **Status:** PASS
- **Targets:** < 2 minutes for 1000 files
- **Measurement:** Benchmark tests with real repository data

## Ready-to-Implement Checklist

### Pre-Implementation
- [x] All test functions written and documented
- [x] Test data fixtures prepared
- [x] CANARY tokens placed in specification
- [x] Tech stack decisions justified
- [x] Constitutional gates validated

### Implementation Ready
- [ ] Create src/ directory structure
- [ ] Implement language detection engine
- [ ] Create DocMetadata models
- [ ] Implement Go documentation processor
- [ ] Implement Zig documentation processor
- [ ] Create cross-reference resolver
- [ ] Implement unified renderer
- [ ] Add comprehensive test suite
- [ ] Create performance benchmarks
- [ ] Add security validations
- [ ] Update CANARY tokens to IMPL status
- [ ] Run full test suite
- [ ] Validate performance targets
- [ ] Update documentation

### Post-Implementation
- [ ] Update CANARY tokens to TESTED status
- [ ] Run canary scan --verify
- [ ] Update requirements tracking
- [ ] Create usage documentation