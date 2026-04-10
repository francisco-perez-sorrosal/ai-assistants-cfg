# Rust Testing

Rust testing patterns, tools, and best practices using the built-in test framework and popular crates. Back to [SKILL.md](../SKILL.md).

## Built-in Test Framework

### Test Organization

Rust has two test categories with distinct conventions:

| Category | Location | Purpose | Runs With |
|----------|----------|---------|-----------|
| **Unit tests** | Inline `#[cfg(test)] mod tests` | Test private functions, isolated logic | `cargo test` |
| **Integration tests** | `tests/` directory | Test public API, cross-module behavior | `cargo test` |
| **Doc tests** | `///` doc comments | Verify documentation examples compile and run | `cargo test --doc` |

### Unit Test Pattern

```rust
// src/parser.rs
pub fn parse_config(input: &str) -> Result<Config, ParseError> {
    // implementation
}

// Private helper -- testable via unit tests
fn normalize_key(key: &str) -> String {
    key.trim().to_lowercase()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_config_valid_input() {
        let input = "key = value";
        let config = parse_config(input).unwrap();
        assert_eq!(config.get("key"), Some("value"));
    }

    #[test]
    fn parse_config_empty_input_returns_error() {
        let result = parse_config("");
        assert!(result.is_err());
    }

    #[test]
    fn normalize_key_trims_and_lowercases() {
        assert_eq!(normalize_key("  MyKey  "), "mykey");
    }
}
```

The `#[cfg(test)]` attribute ensures test code is excluded from release builds. `use super::*` imports all items from the parent module, including private functions.

### Integration Test Pattern

```rust
// tests/api_integration.rs
use my_crate::Client;

#[test]
fn client_fetches_user_by_id() {
    let client = Client::new("http://localhost:8080");
    let user = client.get_user(42).unwrap();
    assert_eq!(user.name, "Alice");
}
```

Each file in `tests/` is compiled as a separate crate. It can only access the public API of your library.

### Shared Test Helpers

```rust
// tests/common/mod.rs
pub fn setup_test_db() -> TestDb {
    // shared setup logic
}

// tests/api_integration.rs
mod common;

#[test]
fn test_with_db() {
    let db = common::setup_test_db();
    // ...
}
```

Use `tests/common/mod.rs` (not `tests/common.rs`) to prevent Cargo from treating the helper as an integration test binary.

## Key Cargo Test Flags

| Flag | Purpose |
|------|---------|
| `cargo test` | Run all tests (unit + integration + doc) |
| `cargo test -- --nocapture` | Show stdout/stderr output from tests |
| `cargo test test_name` | Run tests matching a name pattern |
| `cargo test -- --ignored` | Run only `#[ignore]`-marked tests |
| `cargo test --lib` | Unit tests only |
| `cargo test --test integration` | Specific integration test file |
| `cargo test --doc` | Doc tests only |
| `cargo test -- --test-threads=1` | Run tests sequentially |

## Assertions

### Standard Assertions

```rust
assert!(condition);                              // Boolean check
assert_eq!(left, right);                         // Equality (both must impl Debug)
assert_ne!(left, right);                         // Inequality
assert!(result.is_ok());                         // Result is Ok
assert!(result.is_err());                        // Result is Err
assert_eq!(result.unwrap_err().to_string(), "expected error message");
```

### Custom Error Messages

```rust
assert_eq!(
    actual, expected,
    "Expected {expected} but got {actual} for input '{input}'"
);
```

### Testing Panics

```rust
#[test]
#[should_panic(expected = "index out of bounds")]
fn panics_on_invalid_index() {
    let v = vec![1, 2, 3];
    let _ = v[99];
}
```

### Testing Results

```rust
#[test]
fn returns_error_for_invalid_input() -> Result<(), Box<dyn std::error::Error>> {
    let result = parse("invalid");
    assert!(result.is_err());
    Ok(())
}
```

## Property-Based Testing with proptest

```toml
# Cargo.toml
[dev-dependencies]
proptest = "1"
```

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn roundtrip_encode_decode(input in ".*") {
        let encoded = encode(&input);
        let decoded = decode(&encoded).unwrap();
        assert_eq!(decoded, input);
    }

    #[test]
    fn sort_is_idempotent(mut vec in prop::collection::vec(any::<i32>(), 0..100)) {
        vec.sort();
        let sorted_once = vec.clone();
        vec.sort();
        assert_eq!(vec, sorted_once);
    }
}
```

### Custom Strategies

```rust
use proptest::prelude::*;

#[derive(Debug, Clone)]
struct Config {
    port: u16,
    host: String,
}

fn config_strategy() -> impl Strategy<Value = Config> {
    (1024..65535u16, "[a-z]{3,10}")
        .prop_map(|(port, host)| Config { port, host })
}

proptest! {
    #[test]
    fn config_serialization_roundtrip(config in config_strategy()) {
        let json = serde_json::to_string(&config).unwrap();
        let parsed: Config = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.port, config.port);
    }
}
```

## Mocking

### mockall (Most Popular)

```toml
[dev-dependencies]
mockall = "0.13"
```

```rust
use mockall::automock;

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), DbError>;
}

#[test]
fn service_returns_none_for_missing_user() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .with(eq(42))
        .returning(|_| None);

    let service = UserService::new(Box::new(mock_repo));
    assert!(service.get_user(42).is_none());
}
```

### When to Mock in Rust

- **Mock traits at boundaries**: External services, databases, file systems
- **Do not mock concrete types**: Rust's ownership model makes internal mocking awkward and usually unnecessary
- **Prefer fakes for simple cases**: A `HashMap`-backed in-memory repository is often clearer than a mock

## Async Testing

### tokio

```toml
[dev-dependencies]
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

```rust
#[tokio::test]
async fn async_fetch_returns_data() {
    let client = Client::new();
    let result = client.fetch("https://example.com").await;
    assert!(result.is_ok());
}

// With custom runtime configuration
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn concurrent_operations() {
    // ...
}
```

### Timeout Pattern

```rust
use tokio::time::{timeout, Duration};

#[tokio::test]
async fn operation_completes_within_deadline() {
    let result = timeout(Duration::from_secs(5), async_operation()).await;
    assert!(result.is_ok(), "Operation timed out");
}
```

## Snapshot Testing with insta

```toml
[dev-dependencies]
insta = { version = "1", features = ["yaml"] }
```

```rust
use insta::assert_yaml_snapshot;

#[test]
fn api_response_format() {
    let response = build_response(test_data());
    assert_yaml_snapshot!(response);
}
```

```bash
# Review and accept snapshots
cargo insta review

# Update all snapshots
cargo insta accept
```

Snapshot files are stored in `src/snapshots/` (or `tests/snapshots/` for integration tests). Commit them to version control.

## Test Fixtures with rstest

```toml
[dev-dependencies]
rstest = "0.23"
```

### Parameterized Tests

```rust
use rstest::rstest;

#[rstest]
#[case("hello", 5)]
#[case("", 0)]
#[case("rust", 4)]
fn string_length(#[case] input: &str, #[case] expected: usize) {
    assert_eq!(input.len(), expected);
}
```

### Fixtures

```rust
use rstest::*;

#[fixture]
fn test_config() -> Config {
    Config::builder()
        .port(8080)
        .host("localhost")
        .build()
}

#[rstest]
fn server_starts_with_config(test_config: Config) {
    let server = Server::new(test_config);
    assert!(server.start().is_ok());
}
```

## Code Coverage

### cargo-llvm-cov (Recommended)

```bash
cargo install cargo-llvm-cov

cargo llvm-cov                 # Run tests with coverage
cargo llvm-cov --html          # Generate HTML report
cargo llvm-cov --lcov > lcov.info  # LCOV format for CI
```

### cargo-tarpaulin (Alternative)

```bash
cargo install cargo-tarpaulin

cargo tarpaulin --out html     # HTML report
cargo tarpaulin --out xml      # Cobertura XML for CI
```

## Gotchas

- **Tests run in parallel by default**: Use `-- --test-threads=1` or synchronization primitives when tests share resources (files, ports, global state).
- **`#[should_panic]` tests cannot return `Result`**: Choose one or the other. For error assertions, prefer `Result`-returning tests with explicit `is_err()` checks.
- **Doc tests are slow**: Each doc test is compiled as a separate binary. Use `#[cfg(doctest)]` attributes to control compilation. For large crates, run `--doc` separately from `--lib`.
- **Integration tests see only `pub` items**: If you need to test internal behavior, use unit tests in `#[cfg(test)] mod tests`.
- **`cargo test` compiles tests as debug**: Tests may pass in debug but fail in release due to integer overflow checks. Periodically run `cargo test --release`.
- **Temporary directories**: Use `tempfile::tempdir()` instead of hardcoded paths. The directory is automatically cleaned up when the `TempDir` guard is dropped.
