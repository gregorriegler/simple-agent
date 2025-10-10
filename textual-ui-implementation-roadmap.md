# Textual UI Implementation Roadmap

## Executive Summary

This roadmap provides a step-by-step guide for implementing a flexible UI architecture that supports multiple backends (Console, Textual, Web) while maintaining the existing clean architecture principles of the simple-agent project.

## Key Architectural Decisions

### 1. Protocol-First Design
- Maintain existing protocol-based architecture
- Extend protocols to support richer UI interactions
- Ensure backward compatibility with current console interface

### 2. Backend Registry Pattern
- Centralized registration of UI backends
- Runtime backend selection based on configuration
- Easy extensibility for future UI technologies

### 3. Event-Driven Communication
- Decouple UI interactions from business logic
- Enable async/sync compatibility across backends
- Support rich UI features like real-time updates

### 4. Configuration-Driven Behavior
- Support multiple configuration sources (CLI, file, env)
- Backend-specific configuration options
- Sensible defaults for zero-configuration usage

## Implementation Phases

### Phase 1: Foundation Refactoring (Week 1-2)

#### Goals
- Extract and enhance UI protocols
- Create backend registry system
- Refactor main entry point

#### Tasks
1. **Create new UI protocol structure**
   ```bash
   mkdir -p simple_agent/application/ui
   mkdir -p simple_agent/application/events
   mkdir -p simple_agent/application/config
   ```

2. **Implement enhanced protocols**
   - [`DisplayProtocol`](simple_agent/application/ui/display_protocol.py) with rich message support
   - [`InputProtocol`](simple_agent/application/ui/input_protocol.py) with async capabilities
   - [`UIBackendProtocol`](simple_agent/application/ui/backend_protocol.py) for backend abstraction

3. **Create backend registry**
   - [`BackendRegistry`](simple_agent/application/ui/backend_registry.py) for backend management
   - [`BackendFactory`](simple_agent/application/ui/backend_factory.py) for backend creation

4. **Refactor main entry point**
   - Update [`main()`](simple_agent/main.py:15) to use backend factory
   - Add command-line arguments for backend selection
   - Maintain backward compatibility

#### Success Criteria
- All existing tests pass
- Console backend works identically to current implementation
- Backend selection mechanism functional

### Phase 2: Console Backend Migration (Week 2-3)

#### Goals
- Move existing console code to new structure
- Implement console backend using new protocols
- Ensure feature parity

#### Tasks
1. **Create console backend structure**
   ```bash
   mkdir -p simple_agent/infrastructure/ui/console
   ```

2. **Migrate existing console components**
   - Move [`ConsoleDisplay`](simple_agent/infrastructure/console_display.py:11) to new location
   - Move [`ConsoleUserInput`](simple_agent/infrastructure/console_user_input.py:6) to new location
   - Update imports and references

3. **Implement [`ConsoleUIBackend`](simple_agent/infrastructure/ui/console/console_backend.py)**
   - Integrate existing console components
   - Implement new protocol methods
   - Handle configuration options

4. **Update tests**
   - Migrate existing console tests
   - Add backend-specific tests
   - Ensure integration tests pass

#### Success Criteria
- Console backend fully functional
- All existing functionality preserved
- Test coverage maintained

### Phase 3: Configuration System (Week 3-4)

#### Goals
- Implement comprehensive configuration system
- Support multiple configuration sources
- Add validation and error handling

#### Tasks
1. **Create configuration structure**
   - [`UIConfig`](simple_agent/application/config/ui_config.py) dataclass
   - [`ConfigLoader`](simple_agent/application/config/config_loader.py) with multiple sources
   - Configuration validation

2. **Add command-line support**
   - `--ui` flag for backend selection
   - `--theme` flag for theme selection
   - Backend-specific options

3. **Add configuration file support**
   - `.simple-agent.toml` parsing
   - Environment variable support
   - Configuration precedence rules

4. **Error handling and validation**
   - Invalid backend handling
   - Configuration validation
   - Helpful error messages

#### Success Criteria
- Multiple configuration sources working
- Proper error handling and validation
- Documentation for configuration options

### Phase 4: Textual Backend Implementation (Week 4-6)

#### Goals
- Implement full Textual UI backend
- Create rich interactive interface
- Support all agent features

#### Tasks
1. **Add dependencies**
   ```toml
   # Add to pyproject.toml
   textual = ">=0.41.0"
   rich = ">=13.0.0"
   ```

2. **Create Textual backend structure**
   ```bash
   mkdir -p simple_agent/infrastructure/ui/textual/widgets
   mkdir -p simple_agent/infrastructure/ui/textual/themes
   ```

3. **Implement core Textual components**
   - [`TextualApp`](simple_agent/infrastructure/ui/textual/textual_app.py) main application
   - [`TextualBackend`](simple_agent/infrastructure/ui/textual/textual_backend.py) backend implementation
   - [`TextualDisplay`](simple_agent/infrastructure/ui/textual/textual_display.py) and [`TextualInput`](simple_agent/infrastructure/ui/textual/textual_input.py)

4. **Create UI widgets**
   - [`ChatWidget`](simple_agent/infrastructure/ui/textual/widgets/chat_widget.py) for conversation display
   - [`InputWidget`](simple_agent/infrastructure/ui/textual/widgets/input_widget.py) for user input
   - [`StatusWidget`](simple_agent/infrastructure/ui/textual/widgets/status_widget.py) for session status

5. **Implement event handling**
   - User input events
   - Assistant message events
   - Tool result events
   - Session status events

6. **Add theming support**
   - Default theme
   - Dark/light theme variants
   - Custom CSS support

#### Success Criteria
- Fully functional Textual interface
- All agent features supported
- Responsive and intuitive UI
- Theme support working

### Phase 5: Event System Integration (Week 5-6)

#### Goals
- Implement event bus for UI-agnostic communication
- Enable real-time UI updates
- Support async operations

#### Tasks
1. **Create event system**
   - [`EventBus`](simple_agent/application/events/event_bus.py) implementation
   - [`UIEvent`](simple_agent/application/events/ui_events.py) types
   - Event subscription/publishing

2. **Integrate with Agent**
   - Update [`Agent`](simple_agent/application/agent.py:7) to use events
   - Async/sync compatibility layer
   - Event-driven UI updates

3. **Backend event handling**
   - Console backend event handling
   - Textual backend event handling
   - Real-time updates

#### Success Criteria
- Event system fully functional
- Real-time UI updates working
- Async/sync compatibility maintained

### Phase 6: Testing and Quality Assurance (Week 6-7)

#### Goals
- Comprehensive test coverage
- Performance optimization
- Documentation completion

#### Tasks
1. **Unit testing**
   - Protocol implementations
   - Backend functionality
   - Configuration system
   - Event system

2. **Integration testing**
   - End-to-end backend testing
   - Cross-backend compatibility
   - Configuration integration

3. **UI testing**
   - Console UI automation
   - Textual UI simulation
   - User interaction testing

4. **Performance testing**
   - Backend switching performance
   - Event system overhead
   - Memory usage optimization

5. **Documentation**
   - User guide for new features
   - Developer documentation
   - Configuration reference

#### Success Criteria
- >90% test coverage
- Performance benchmarks met
- Complete documentation

## Technical Implementation Details

### Key Files to Create

```
simple_agent/
├── application/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── backend_protocol.py      # UIBackendProtocol definition
│   │   ├── backend_registry.py      # Backend registration system
│   │   ├── backend_factory.py       # Backend creation logic
│   │   ├── display_protocol.py      # Enhanced DisplayProtocol
│   │   ├── input_protocol.py        # Enhanced InputProtocol
│   │   └── ui_manager.py           # Central UI management
│   ├── events/
│   │   ├── __init__.py
│   │   ├── event_bus.py            # Event system implementation
│   │   └── ui_events.py            # UI event definitions
│   └── config/
│       ├── __init__.py
│       ├── ui_config.py            # Configuration dataclasses
│       └── config_loader.py        # Configuration loading logic
├── infrastructure/
│   └── ui/
│       ├── console/
│       │   ├── __init__.py
│       │   ├── console_backend.py   # Console backend implementation
│       │   ├── console_display.py   # Migrated console display
│       │   └── console_input.py     # Migrated console input
│       └── textual/
│           ├── __init__.py
│           ├── textual_backend.py   # Textual backend implementation
│           ├── textual_app.py       # Main Textual application
│           ├── textual_display.py   # Textual display implementation
│           ├── textual_input.py     # Textual input implementation
│           ├── widgets/
│           │   ├── __init__.py
│           │   ├── chat_widget.py   # Chat conversation widget
│           │   ├── input_widget.py  # User input widget
│           │   └── status_widget.py # Status display widget
│           └── themes/
│               ├── __init__.py
│               └── default.py       # Default theme definitions
```

### Key Dependencies to Add

```toml
# pyproject.toml additions
[project]
dependencies = [
    "piper-tts>=1.3.0",
    "pygame>=2.6.1", 
    "requests",
    "textual>=0.41.0",    # For TUI backend
    "rich>=13.0.0",       # Enhanced console output
]
```

### Command Line Interface Changes

```bash
# Current usage (unchanged)
agent "Hello world"

# New backend selection options
agent --ui console "Hello world"      # Explicit console
agent --ui textual "Hello world"      # Textual TUI
agent --ui textual --theme dark "Hello world"  # With theme

# Configuration file usage
agent --config ~/.simple-agent.toml "Hello world"
```

### Configuration File Format

```toml
# .simple-agent.toml
[ui]
backend = "textual"
theme = "dark"

[ui.console]
indent_level = 0
agent_name = "Agent"
color_output = true

[ui.textual]
enable_mouse = true
enable_animations = true
chat_history_limit = 1000
custom_css = "~/.simple-agent-theme.css"

[ui.features]
rich_input = true
file_upload = false
auto_scroll = true
```
