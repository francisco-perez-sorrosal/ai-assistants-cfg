---
name: Refactoring
description: Pragmatic refactoring practices emphasizing modularity, low coupling, high cohesion, and incremental improvement. Use when restructuring code, improving design, reducing coupling, or organizing codebases for better maintainability.
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, TodoWrite]
---

# Pragmatic Refactoring

Systematic approach to refactoring that prioritizes modularity, low coupling, high cohesion, and maintainable structure.

## Core Principles

**Pragmatism First**: Every refactoring must have a clear purpose. Never refactor for the sake of refactoring.

**Small, Bold Steps**: Make incremental changes that keep the system working. Each step should be independently committable.

**Behavior Preservation**: Refactoring changes structure, not behavior. Tests should pass before and after.

**Simplicity Over Cleverness**: The simplest solution that solves the problem is the best solution.

## The Four Pillars

### 1. Modularity

**What**: Break systems into self-contained units with clear responsibilities.

**Why**: Enables understanding, testing, and changing parts independently.

**How**:
- Each module should have a single, well-defined purpose
- Modules should be understandable in isolation
- Clear boundaries between modules
- Prefer many small, focused modules over few large ones

**Example**:
```python
# Before: Everything in one module
class UserManager:
    def validate_email(self, email): ...
    def hash_password(self, password): ...
    def send_welcome_email(self, user): ...
    def store_in_database(self, user): ...
    def log_activity(self, action): ...

# After: Separated by concern
# user_validation.py
def validate_email(email: str) -> bool: ...

# password_security.py
def hash_password(password: str) -> str: ...

# email_service.py
def send_welcome_email(user: User) -> None: ...

# user_repository.py
class UserRepository:
    def store(self, user: User) -> None: ...

# activity_logger.py
def log_activity(action: str) -> None: ...
```

### 2. Low Coupling

**What**: Minimize dependencies between modules.

**Why**: Changes in one module shouldn't force changes in others. Enables independent evolution.

**How**:
- Depend on abstractions, not concrete implementations
- Use dependency injection
- Avoid circular dependencies
- Prefer data over shared state
- Use events/messages for loose communication

**Anti-patterns**:
- Passing entire objects when only one property is needed
- Importing from deep in another module's hierarchy
- Shared mutable state

**Example**:
```python
# Before: Tightly coupled
class OrderProcessor:
    def __init__(self):
        self.db = PostgresDatabase()  # Concrete dependency
        self.emailer = SmtpEmailer()  # Concrete dependency

    def process(self, order):
        self.db.save(order)
        self.emailer.send(order.customer.email)

# After: Loosely coupled via abstractions
from typing import Protocol

class Database(Protocol):
    def save(self, order: Order) -> None: ...

class Emailer(Protocol):
    def send(self, recipient: str, message: str) -> None: ...

class OrderProcessor:
    def __init__(self, db: Database, emailer: Emailer):
        self.db = db
        self.emailer = emailer

    def process(self, order: Order) -> None:
        self.db.save(order)
        self.emailer.send(order.customer.email, order.format_message())
```

### 3. High Cohesion

**What**: Keep related things together, unrelated things apart.

**Why**: Makes code easier to understand and change. Clear where to look for functionality.

**How**:
- Group functions/classes by what they do together
- If you frequently change A and B together, they belong together
- If A and B serve different purposes, separate them
- Follow the "one reason to change" principle

**Example**:
```python
# Before: Low cohesion
# utils.py
def format_date(date): ...
def validate_email(email): ...
def calculate_discount(price, percent): ...
def send_notification(user): ...

# After: High cohesion
# date_formatting.py
def format_date(date: datetime) -> str: ...
def parse_date(date_str: str) -> datetime: ...

# email_validation.py
def validate_email(email: str) -> bool: ...
def normalize_email(email: str) -> str: ...

# pricing.py
def calculate_discount(price: Decimal, percent: int) -> Decimal: ...
def apply_tax(price: Decimal, rate: float) -> Decimal: ...

# notifications.py
def send_notification(user: User, message: str) -> None: ...
```

### 4. Pragmatic Structure

**What**: Organize code in a way that matches how you think about and work with the domain.

**Why**: Makes the codebase navigable and intuitive.

**How**:
- Structure should reflect domain concepts, not technical layers
- Prefer feature-based organization over layer-based
- Package by component, not by type
- Use meaningful names that match domain language

**Example**:
```
# Before: Layer-based (technical grouping)
project/
├── models/
│   ├── user.py
│   ├── order.py
│   └── product.py
├── controllers/
│   ├── user_controller.py
│   ├── order_controller.py
│   └── product_controller.py
└── services/
    ├── user_service.py
    ├── order_service.py
    └── product_service.py

# After: Feature-based (domain grouping)
project/
├── users/
│   ├── user.py
│   ├── user_repository.py
│   ├── user_service.py
│   └── authentication.py
├── orders/
│   ├── order.py
│   ├── order_repository.py
│   ├── order_processing.py
│   └── order_validation.py
└── catalog/
    ├── product.py
    ├── product_repository.py
    └── pricing.py
```

## Refactoring Patterns

### Extract Module

**When**: A file or class has multiple responsibilities.

**How**:
1. Identify cohesive groups of functions/methods
2. Create new module for each group
3. Move functions maintaining their signatures
4. Update imports
5. Run tests

### Introduce Abstraction

**When**: Concrete dependencies make code hard to test or change.

**How**:
1. Define Protocol or abstract base class
2. Make dependent code accept the abstraction
3. Keep concrete implementation separate
4. Inject dependency

### Eliminate Circular Dependencies

**When**: Module A imports B, B imports A (or longer cycles).

**How**:
1. Identify the cycle with dependency analysis
2. Extract common dependencies to new module
3. Use dependency inversion (depend on abstractions)
4. Consider if modules should be merged

### Extract Data Structure

**When**: Functions pass many related parameters around.

**How**:
1. Group related parameters into dataclass/namedtuple
2. Pass single data structure instead
3. Makes function signatures cleaner
4. Easier to evolve

```python
# Before
def create_user(name: str, email: str, age: int, city: str, country: str) -> User:
    ...

# After
@dataclass(frozen=True)
class UserData:
    name: str
    email: str
    age: int
    city: str
    country: str

def create_user(data: UserData) -> User:
    ...
```

### Inline Over-Abstraction

**When**: Abstraction serves only one use case or adds no value.

**How**:
1. Identify abstractions with single implementation
2. Inline the abstraction
3. Simplify the code
4. Add abstraction back if second use case appears

**Remember**: Abstractions have cost. Only add when multiple concrete cases exist.

## Refactoring Workflow

### 1. Understand Current State

Before refactoring:
- Read and understand the code
- Identify what's working, what's painful
- Run existing tests (or write characterization tests)
- Document current behavior if unclear

### 2. Plan the Change

- Define clear goal: "Extract payment processing from order service"
- Break into small steps
- Each step should be safe and testable
- Use TodoWrite to track steps

### 3. Execute Incrementally

- Make one small change at a time
- Run tests after each change
- Commit after each successful step
- If tests fail, fix or revert

### 4. Verify and Clean Up

- All tests pass
- No dead code left behind
- Imports are clean
- Documentation updated if needed

## Decision Framework

### Should I Create a New Module?

**Yes, if**:
- Clear boundary and single responsibility
- Code is used by multiple other modules
- Natural cohesion within the module
- Reduces coupling in existing modules

**No, if**:
- Only one use case
- Creates artificial separation
- Increases complexity without benefit
- Code is tightly coupled to one specific module

### Should I Add an Abstraction?

**Yes, if**:
- Multiple implementations exist or will soon
- Need to swap implementations (testing, config)
- Reducing coupling between modules
- Clear interface with meaningful semantics

**No, if**:
- Only one implementation exists and likely will
- Abstraction doesn't hide complexity
- "Might need it someday" (YAGNI)
- Makes code harder to understand

### Should I Split This Package?

**Yes, if**:
- Package has multiple unrelated responsibilities
- Different parts change for different reasons
- High coupling within subgroups, low coupling between
- Package is becoming too large to grasp

**No, if**:
- Everything in package changes together
- High cohesion across all parts
- Splitting would increase coupling
- Package is small and focused

## Common Refactoring Scenarios

### Scenario: God Object/Module

**Signs**: One class/module doing everything, hundreds of lines, many dependencies.

**Solution**:
1. List all responsibilities
2. Group by cohesion
3. Extract each group to focused module
4. Use composition to reconnect

### Scenario: Feature Envy

**Signs**: Method uses more data/methods from another class than its own.

**Solution**:
1. Move method to the class it envies
2. Or extract the envied data into its own concept
3. Reduce coupling by passing only needed data

### Scenario: Primitive Obsession

**Signs**: Using primitives (strings, ints) where domain concepts exist.

**Solution**:
1. Create value object/dataclass for concept
2. Add validation and behavior to the type
3. Replace primitive usage

```python
# Before
def process_email(email: str) -> None:
    if "@" not in email:
        raise ValueError("Invalid email")
    normalized = email.lower().strip()
    ...

# After
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError("Invalid email")
        object.__setattr__(self, 'value', self.value.lower().strip())

def process_email(email: Email) -> None:
    # email is guaranteed valid and normalized
    ...
```

### Scenario: Utils Hell

**Signs**: Growing utils module with unrelated functions.

**Solution**:
1. Audit what's actually used
2. Delete unused functions
3. Move functions to domain modules they support
4. Only keep truly generic utilities

**Exception**: Only use generic `utils.py` for functions so fundamental they belong nowhere else.

### Scenario: Deep Nesting

**Signs**: Many levels of indentation, hard to follow logic.

**Solution**:
1. Extract nested blocks to functions
2. Invert conditions (early return)
3. Use guard clauses
4. Flatten with extraction

```python
# Before
def process_order(order):
    if order.is_valid():
        if order.customer.is_active():
            if order.payment.is_authorized():
                if order.inventory_available():
                    # Deep nested logic
                    ...

# After
def process_order(order: Order) -> None:
    if not order.is_valid():
        raise InvalidOrderError()

    if not order.customer.is_active():
        raise InactiveCustomerError()

    if not order.payment.is_authorized():
        raise PaymentNotAuthorizedError()

    if not order.inventory_available():
        raise InsufficientInventoryError()

    # Logic at top level
    ...
```

## Anti-Patterns to Avoid

### Over-Abstraction

Creating interfaces/protocols/base classes without multiple concrete implementations.

**Fix**: Start concrete, extract abstraction when second use case appears.

### Anemic Models

Data classes with no behavior, all logic in external services.

**Fix**: Move behavior that belongs to the concept into the class.

### Shotgun Surgery

One change requires modifications in many files.

**Fix**: Increase cohesion—group things that change together.

### Speculative Generality

Adding flexibility for hypothetical future needs.

**Fix**: Implement for current requirements. Refactor when new requirements appear.

### Premature Optimization

Refactoring for performance without measurements.

**Fix**: Profile first, optimize hot paths only, maintain clarity.

## Tools and Techniques

### Dependency Analysis

Identify coupling hotspots:
```bash
# Python: Find import dependencies
grep -r "^import\|^from" . --include="*.py" | sort | uniq -c | sort -rn

# Find circular dependencies
# Use tools like pydeps, import-linter
```

### Code Metrics

Monitor complexity:
- **Lines of code**: Modules >500 lines need review
- **Cyclomatic complexity**: Functions >10 need simplification
- **Coupling**: Count dependencies per module
- **Cohesion**: Measure internal relatedness

### Safe Refactoring Steps

1. **Green Bar**: Ensure all tests pass
2. **Small Change**: One small refactoring
3. **Run Tests**: Verify behavior unchanged
4. **Commit**: Save working state
5. **Repeat**: Next small step

## Language-Specific Guidance

### Python

- Use Protocols for abstractions (PEP 544)
- Dataclasses for immutable data
- Avoid deep inheritance hierarchies
- Prefer composition over inheritance
- Type hints enable safe refactoring

### General Principles (Language Agnostic)

- Pure functions (no side effects) are easiest to refactor
- Immutable data reduces coupling
- Explicit dependencies over implicit
- Favor readability in common cases, optimization in proven bottlenecks

## When NOT to Refactor

**Don't refactor if**:
- No tests exist and behavior is unclear (write tests first)
- Code is about to be deleted
- Working code with no current pain point
- Refactoring for resume-driven development
- Team doesn't understand the pattern you're introducing

**Do refactor when**:
- Adding feature and current structure is obstacle
- Bug reveals structural problem
- Code duplication reaches three instances
- Coupling prevents testing
- Team struggles to understand code

## Summary Checklist

Before committing refactoring:

- [ ] All tests pass
- [ ] No behavior changes
- [ ] Coupling reduced or unchanged
- [ ] Cohesion improved
- [ ] Code is more readable
- [ ] No dead code remains
- [ ] Imports are clean
- [ ] Each module has clear purpose
- [ ] Dependencies are explicit
- [ ] Can explain why each change improves design

**Remember**: The best refactoring is the one that makes the next change easier.
